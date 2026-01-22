from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt.tool_node import ToolNode

load_dotenv()

# -------------------------
# Tools
# -------------------------

@tool
def calculator(a: float, b: float) -> str:
    """Perform basic arithmetic addition."""
    print("calculator tool called")
    return f"The sum of {a} and {b} is {a + b}"

@tool
def say_hello(name: str) -> str:
    """Greet a user by name."""
    print("say_hello tool called")
    return f"Hello {name}, I hope you are well today."

tools = [calculator, say_hello]

# -------------------------
# Model
# -------------------------

model = ChatOpenAI(
    model="gpt-5-nano",
    temperature=0
)

# -------------------------
# State Definition
# -------------------------

class AgentState(dict):
    messages: list

# -------------------------
# Nodes
# -------------------------

def agent_node(state: AgentState):
    response = model.invoke(state["messages"])
    return {"messages": [response]}

tool_node = ToolNode(tools)

# -------------------------
# Graph
# -------------------------

workflow = StateGraph(AgentState)

workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    lambda state: "tools" if state["messages"][-1].tool_calls else END,
)

workflow.add_edge("tools", "agent")

workflow = workflow.compile()

# -------------------------
# Main Loop
# -------------------------

def main():
    print("Welcome! I'm your AI assistant. Type 'quit' to exit.")

    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() == "quit":
            break

        print("\nAssistant: ", end="", flush=True)

        for chunk in workflow.stream(
            {"messages": [HumanMessage(content=user_input)]},
            stream_mode="values",
        ):
            if "messages" in chunk:
                for message in chunk["messages"]:
                    if isinstance(message, AIMessage):
                        print(message.content, end="", flush=True)

        print()

if __name__ == "__main__":
    main()
