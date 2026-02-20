from typing import TypedDict, Annotated, List
import operator
from langgraph.graph import StateGraph

# Define the state with a reducer for messages (concatenation)
class State(TypedDict):
    values: List[int]
    name: str
    result: str
    operation: str

def process_value(state: State) -> State:
    """This function handles multiple different inputs"""
    values = state["values"]
    name = state["name"]
    operation = state["operation"]

    if operation == "+":
        total = 0
        for i in values:
            total += i
        state["result"] = f"Hi {name}, your answer is {total}"
    elif operation == "-":
        total = 0
        for i in values:
            total -= i
        state["result"] = f"Hi {name}, your answer is {total}"
    elif operation == "*":
        total = 1
        for i in values:
            total *= i
        state["result"] = f"Hi {name}, your answer is {total}"
    elif operation == "/":
        total = 1
        for i in values:
            total /= i
        state["result"] = f"Hi {name}, your answer is {total}"    
    else:
        state["result"] = f"Hi {name}, I don't know what to do"
    return state

# Build the graph
builder = StateGraph(State)
builder.add_node("process_value", process_value)
builder.set_entry_point("process_value")
builder.set_finish_point("process_value")

graph = builder.compile()

# Invoke with input
state = graph.invoke({"name": "Bay", "values": [1, 2, 3,4], "operation": "*"})
print(state["result"])