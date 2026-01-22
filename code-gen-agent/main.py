from llama_index.llms.ollama import Ollama
from llama_parse import LlamaParse
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    PromptTemplate,
    Settings,
)
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.agent import ReActAgent
from llama_index.core.output_parsers import PydanticOutputParser
from llama_index.core.query_pipeline import QueryPipeline
from pydantic import BaseModel
from dotenv import load_dotenv

from prompts import context, code_parser_template
from code_reader import code_reader

import os

load_dotenv()
os.makedirs("output", exist_ok=True)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")

Settings.llm = Ollama(
    model="qwen2.5:3b", 
    base_url=OLLAMA_BASE_URL, 
    request_timeout=120.0,
    temperature=0.2
)

pdf_parser = LlamaParse(result_type="markdown")

documents = SimpleDirectoryReader(
    "./data", 
    file_extractor={".pdf": pdf_parser},
).load_data()

Settings.embed_model = OllamaEmbedding(
    model_name="nomic-embed-text", 
    base_url=OLLAMA_BASE_URL
)

vector_index = VectorStoreIndex.from_documents(documents)

query_engine = vector_index.as_query_engine(
    llm=Settings.llm
)

tools = [
    code_reader,
    QueryEngineTool(
        query_engine=query_engine,
        metadata=ToolMetadata(
            name="api_documentation",
            description="Provides API documentation context from indexed documents",
        ),
    ),
]

code_llm = Ollama(
    model="qwen2.5-coder:3b", 
    base_url=OLLAMA_BASE_URL,
    request_timeout=180.0,
    temperature=0.1)

agent = ReActAgent.from_tools(
    tools=tools, 
    llm=code_llm, 
    verbose=True, 
    context=context,
)

class CodeOutput(BaseModel):
    code: str
    description: str
    filename: str

output_parser = PydanticOutputParser(CodeOutput)

json_prompt = PromptTemplate(
    template=code_parser_template,
    output_parser=output_parser,
)

output_pipeline = QueryPipeline(
    chain=[json_prompt, Settings.llm, output_parser])

while (prompt := input("Enter a prompt (q to quit): ")) != "q":
    retries = 0
    
    while retries < 3:
        try:    
            agent_result = agent.query(prompt)

            parsed: CodeOutput = output_pipeline.run(
                response=agent_result
            )
            break
        except Exception as e:
            retries += 1
            print("Error occured, retry #{retries}:", e)
    
    if retries == 3:
        print("Unable to process request, try again...")
        continue

    print("\n--- Code Generated ---\n")
    print(parsed.code)
    print("\n--- Description ---\n")
    print(parsed.description)

    try:
        output_path = os.path.join("output", parsed.filename)
        with open(output_path, "w") as f:
            f.write(parsed.code)
        print(f"\nSaved file: {parsed.filename}")
    except Exception as e:
        print("Error saving file:", e)