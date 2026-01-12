from llama_index.llms.ollama import Ollama
from llama_index.core import Settings
from dotenv import load_dotenv
import os

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")

Settings.llm = Ollama(model="ministral-3:8b", base_url=OLLAMA_BASE_URL, request_timeout=120.0)

result = Settings.llm.complete("hello world")
print(result.text)