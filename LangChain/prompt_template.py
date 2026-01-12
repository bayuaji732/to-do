from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(model="gpt-5-nano")

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant that translates {input_language} to {output_language}."),
    ("human", "{text}")
])

# Create chain
chain = prompt | llm

# Invoke chain
result = chain.invoke({
    "input_language": "English",
    "output_language": "French",
    "text": "I love coding."
})

print(result.content)