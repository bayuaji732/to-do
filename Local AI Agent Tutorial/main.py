from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from vector import retriever

from dotenv import load_dotenv
import os

load_dotenv()

ollama_base_url = os.getenv("OLLAMA_BASE_URL")
ollama_model_name = os.getenv("OLLAMA_MODEL_NAME")

model = OllamaLLM(model=ollama_model_name, base_url=ollama_base_url)

template = """
You are an expert in answering questions about a pizza restaurant

Here a some relevant reviews: {reviews}

Here is the question to answer: {question}
"""

prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

while True:
    print("\n\n-------------------------------")
    question = input("Ask your question (q to quit): ")
    print("\n\n")
    if question == "q":
        break
    
    reviews =retriever.invoke(question)
    result = chain.invoke({"reviews": reviews, "question": question})
    print(result)