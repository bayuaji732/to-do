import os
os.environ['USER_AGENT'] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"

from typing import List, TypedDict
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import END, StateGraph, START
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

urls = [
    "https://ryanocm.substack.com/p/123-how-tiny-experiments-can-lead",
    "https://ryanocm.substack.com/p/122-life-razor-the-one-sentence-that",
    "https://ryanocm.substack.com/p/121-warren-buffetts-255-strategy",
    "https://ryanocm.substack.com/p/120-30-years-on-earth-11-habits-that",
]
docs = [WebBaseLoader(url).load() for url in urls]
docs_list = [item for sublist in docs for item in sublist]
text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=250, chunk_overlap=0
)
doc_splits = text_splitter.split_documents(docs_list)
# Add to vectorDB
vectorstore = Chroma.from_documents(
    documents=doc_splits,
    collection_name="rag-chroma",
    embedding=OpenAIEmbeddings(),
)
retriever = vectorstore.as_retriever()


def create_structured_llm(model, schema):
    llm = ChatOpenAI(model=model, temperature=0)
    return llm.with_structured_output(schema)

def create_grading_prompt(system_message, human_template):
    return ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("human", human_template),
    ])

class BinaryScoreModel(BaseModel):
    binary_score: str = Field(description="A binary score of 'yes' or 'no'")


# Retrieval evaluator
retrieval_evaluator_llm = create_structured_llm("gpt-4o-mini", BinaryScoreModel)
retrieval_evaluator_prompt = create_grading_prompt(
    "You are a document retrieval evaluator responsible for checking the relevancy of a retrieved document to the user's question. \n If the document contains keyword(s) or semantic meaning related to the question, grade it as relevant. \n Output a binary score 'yes' or 'no'.",
    "Retrieved document: \n\n {document} \n\n User question: {question}"
)
retrieval_grader = retrieval_evaluator_prompt | retrieval_evaluator_llm


#Hallucination grader
hallucination_grader = create_grading_prompt(
    "You are a grader assessing whether an LLM generation is grounded in / supported by a set of retrieved facts. \n Give a binary score 'yes' or 'no'. 'Yes' means that the answer is grounded in / supported by the set of facts.",
    "Set of facts: \n\n {documents} \n\n LLM generation: {generation}"
) | create_structured_llm("gpt-4o-mini", BinaryScoreModel)


# Answer grader
answer_grader = create_grading_prompt(
    "You are a grader assessing whether an answer addresses / resolves a question. \n Give a binary score 'yes' or 'no'. 'Yes' means that the answer resolves the question.",
    "User question: \n\n {question} \n\n LLM generation: {generation}"
) | create_structured_llm("gpt-4o-mini", BinaryScoreModel)


# Question rewriter
question_rewriter = create_grading_prompt(
    "You are a question re-writer that converts an input question to a better version optimized for vectorstore retrieval. Look at the input and try to reason about the underlying semantic intent / meaning.",
    "Here is the initial question: \n\n {question} \n Formulate an improved question."
) | ChatOpenAI(model="gpt-4o-mini", temperature=0) | StrOutputParser()


# RAG Chain
rag_prompt = ChatPromptTemplate.from_messages([
    ("human", """You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.

Question: {question}

Context: {context}

Answer:""")
])
rag_llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)
rag_chain = rag_prompt | rag_llm | StrOutputParser()




class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        question: question
        generation: LLM generation
        documents: list of documents
    """

    question: str
    generation: str
    documents: List[str]


def retrieve(state):
    print("---RETRIEVE---")
    question = state["question"]
    documents = retriever.invoke(question)
    return {"documents": documents, "question": question}


def generate(state):
    print("---GENERATE---")
    return {
        "documents": state["documents"],
        "question": state["question"],
        "generation": rag_chain.invoke({"context": state["documents"], "question": state["question"]})
    }


def grade_documents(state):
    print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
    question = state["question"]
    documents = state["documents"]

    filtered_docs = [d for d in documents if retrieval_grader.invoke({"question": question, "document": d.page_content}).binary_score == "yes"]

    for d in documents:
        grade = retrieval_grader.invoke({"question": question, "document": d.page_content}).binary_score
        print(f"---GRADE: DOCUMENT {'RELEVANT' if grade == 'yes' else 'NOT RELEVANT'}---")

    return {"documents": filtered_docs, "question": question}


def transform_query(state):
    print("---TRANSFORM QUERY---")
    return {"documents": state["documents"], "question": question_rewriter.invoke({"question": state["question"]})}


def decide_to_generate(state):
    print("---ASSESS GRADED DOCUMENTS---")
    if not state["documents"]:
        print("---DECISION: ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, TRANSFORM QUERY---")
        return "transform_query"
    print("---DECISION: GENERATE---")
    return "generate"


def grade_generation_v_documents_and_question(state):
    print("---CHECK HALLUCINATIONS---")

    hallucination_score = hallucination_grader.invoke({"documents": state["documents"], "generation": state["generation"]}).binary_score
    if hallucination_score == "yes":
        print("---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---")
        answer_score = answer_grader.invoke({"question": state["question"], "generation": state["generation"]}).binary_score
        if answer_score == "yes":
            print("---DECISION: GENERATION ADDRESSES QUESTION---")
            return "useful"
        print("---DECISION: GENERATION DOES NOT ADDRESS QUESTION---")
        return "not useful"
    print("---DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS, RE-TRY---")
    return "not supported"




workflow = StateGraph(GraphState)

# Define the nodes
workflow.add_node("retrieve", retrieve)  # retrieve
workflow.add_node("grade_documents", grade_documents)  # grade documents
workflow.add_node("generate", generate)  # generatae
workflow.add_node("transform_query", transform_query)  # transform_query

# Build graph
workflow.add_edge(START, "retrieve")
workflow.add_edge("retrieve", "grade_documents")
workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {
        "transform_query": "transform_query",
        "generate": "generate",
    },
)
workflow.add_edge("transform_query", "retrieve")
workflow.add_conditional_edges(
    "generate",
    grade_generation_v_documents_and_question,
    {
        "not supported": "generate",
        "useful": END,
        "not useful": "transform_query",
    },
)

# Compile
app = workflow.compile()

'''
from IPython.display import Image, display
try:
    display(Image(app.get_graph(xray=True).draw_mermaid_png()))
except Exception:
    # This requires some extra dependencies and is optional
    pass
'''

png_bytes = app.get_graph(xray=True).draw_mermaid_png()

with open("graph.png", "wb") as f:
    f.write(png_bytes)

#res = app.invoke({"question": "How to improve relationships"})
#res = app.invoke({"question": "How to cook a bagel?"}, {"recursion_limit": 10})
res = app.invoke({"question": "How to cook a bagel?"})
print(res['generation'])

