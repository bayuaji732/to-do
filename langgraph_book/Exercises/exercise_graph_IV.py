from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class AgentState(TypedDict):
    number1: int
    number2: int
    number3: int
    number4: int
    operation: str
    operation2: str
    finalNumber: int
    finalNumber2: int


def adder(state: AgentState) -> AgentState:
    """This node adds the 2 numbers"""
    
    state["finalNumber"] = state["number1"] + state["number2"]
    return state

def subtractor(state: AgentState) -> AgentState:
    """This node subtracts the 2 numbers"""
    
    state["finalNumber"] = state["number1"] - state["number2"]
    return state

def adder2(state: AgentState) -> AgentState:
    """This node adds the 2 numbers"""
    
    state["finalNumber2"] = state["number3"] + state["number4"]
    return state

def subtractor2(state: AgentState) -> AgentState:
    """This node subtracts the 2 numbers"""
    
    state["finalNumber2"] = state["number3"] - state["number4"]
    return state

def decide_next_node_1(state: AgentState) -> AgentState:
    """This node decides which node to execute next"""
    
    if state["operation"] == "add":
        return "addition_operation"
    elif state["operation"] == "subtract":
        return "subtraction_operation"

def decide_next_node_2(state: AgentState) -> AgentState:
    """This node decides which node to execute next"""
    
    if state["operation2"] == "add":
        return "addition_operation"
    elif state["operation2"] == "subtract":
        return "subtraction_operation"


graph = StateGraph(AgentState)

graph.add_node("add_node", adder)
graph.add_node("subtract_node", subtractor)
graph.add_node("add_node2", adder2)
graph.add_node("subtract_node2", subtractor2)
graph.add_node("router", lambda state: state) # passthrough function
graph.add_node("router2", lambda state: state) # passthrough function

graph.add_edge(START, "router")
graph.add_conditional_edges(
    "router", 
    decide_next_node_1,
    {
        # Edge: Node
        "addition_operation": "add_node",
        "subtraction_operation": "subtract_node",
    })
graph.add_conditional_edges(
    "router2", 
    decide_next_node_2,
    {
        # Edge: Node
        "addition_operation": "add_node2",
        "subtraction_operation": "subtract_node2",
    })
graph.add_edge("add_node", "router2")
graph.add_edge("subtract_node", "router2")
graph.add_edge("add_node2", END)
graph.add_edge("subtract_node2", END)

app = graph.compile()

result = app.invoke({"number1": 10, "number2": 5, "operation": "subtract", "number3": 7, "number4": 2, "operation2": "add"})

print(result)