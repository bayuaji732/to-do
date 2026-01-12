from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import BaseOutputParser
from dotenv import load_dotenv

load_dotenv()

class CommaSeparatedListOutputParser(BaseOutputParser):
    def parse(self, text: str):
        return text.strip().split(", ")

llm = ChatOpenAI(model="gpt-5-nano")

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful assistant who generates comma separated lists.
                A user will pass in a category, and you should generate 5 objects in that category in a comma separated list.
                Only return a comma separated list, and nothing more."""),
    ("human", "{text}")
])

chain = prompt | llm | CommaSeparatedListOutputParser()

result = chain.invoke({"text": "colors"})
print(result)