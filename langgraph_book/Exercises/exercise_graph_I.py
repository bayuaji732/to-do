from typing import TypedDict, Annotated, List
import operator
from langgraph.graph import StateGraph

# Define the state with a reducer for messages (concatenation)
class AgentState(TypedDict):
    name: str
    messages: Annotated[List[str], operator.add]

def compliment_node(state: State):
    name = state["name"]
    compliment = f"{name}, you're doing an amazing job learning LangGraph!"
    # Return a dictionary with the key to update. 
    # Because of the annotated reducer, this list will be concatenated to the existing list.
    return {"messages": [compliment]}

# Build the graph
builder = StateGraph(AgentState)
builder.add_node("compliment", compliment_node)
builder.set_entry_point("compliment")
builder.set_finish_point("compliment")

graph = builder.compile()

# Invoke with input
state = graph.invoke({"name": "Bay", "messages": []})
print(state["messages"][-1])
