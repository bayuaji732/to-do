from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import BaseOutputParser
from dotenv import load_dotenv
import re

load_dotenv()

class MathAnswerParser(BaseOutputParser[dict]):
    def parse(self, text: str) -> dict:
        match = re.search(r"answer = (.+)", text)
        if not match:
            raise ValueError("Output does not contain 'answer = <value>'")
        return {
            "steps": text[:match.start()].strip(),
            "answer": match.group(1).strip()
        }
    
    def get_format_instructions(self) -> str:
        return "Return your final answer exactly as: answer = <answer>"

llm = ChatOpenAI(model="gpt-5-nano")

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful assistant that solves math problems and shows your work.
                Output each step, then return the final answer exactly in the format:
                answer = <answer>
                All lowercase, one space on each side of '='."""),
    ("human", "{problem}")
])

# Create chain
chain = prompt | llm | MathAnswerParser()

result = chain.invoke({"problem": "2x^2 - 5x + 3 = 0"})

print(result["answer"])