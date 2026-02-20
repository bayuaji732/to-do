from typing import TypedDict, Annotated, List
import operator
from langgraph.graph import StateGraph

# Define the state with a reducer for messages (concatenation)
class AgentState(TypedDict):
    name: str
    age: int
    skills: str
    final: str

def first_node(state: AgentState) -> AgentState:
    """This is the first node of our sequence"""

    state["final"] = f"{state['name']}, welcome to the system!"
    return state

def second_node(state: AgentState) -> AgentState:
    """This is the second node of our sequence"""

    state["final"] = state["final"] + f" You are {state['age']} years old!"
    return state

def third_node(state: AgentState) -> AgentState:
    """This is the third node of our sequence"""

    state["final"] = state["final"] + f" You have skills in: {state['skills']}"
    return state

# Build the graph
builder = StateGraph(AgentState)
builder.add_node("first_node", first_node)
builder.add_node("second_node", second_node)
builder.add_node("third_node", third_node)
builder.set_entry_point("first_node")
builder.add_edge("first_node", "second_node")
builder.add_edge("second_node", "third_node")
builder.set_finish_point("third_node")

graph = builder.compile()

# Invoke with input
state = graph.invoke({"name": "Bay", "age": 25, "skills": "Python, Machine Learning, and LangGraph"})
print(state["final"])