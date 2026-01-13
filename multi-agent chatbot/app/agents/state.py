"""
State management for the multi-agent system.
"""
from typing import List, Dict, Any, Optional, TypedDict, Annotated
from enum import Enum
import operator


class AgentType(Enum):
    """Types of agents in the system."""
    INTENT = "intent"
    PLANNER = "planner"
    DATA_RETRIEVAL = "data_retrieval"
    ANALYSIS = "analysis"
    VISUALIZATION = "visualization"
    SYNTHESIS = "synthesis"


class QueryIntent(Enum):
    """Types of user query intents."""
    LOOKUP = "lookup"  # Simple data retrieval
    COMPARISON = "comparison"  # Compare entities
    AGGREGATION = "aggregation"  # Sum, average, count, etc.
    RANKING = "ranking"  # Top N, bottom N
    TREND = "trend"  # Time-based analysis
    CORRELATION = "correlation"  # Relationship between variables
    FILTER = "filter"  # Filter based on conditions
    VISUALIZATION = "visualization"  # Explicit chart request
    UNCLEAR = "unclear"  # Ambiguous intent


class ExecutionStep(TypedDict):
    """A single step in the execution plan."""
    step_id: int
    agent_type: AgentType
    description: str
    dependencies: List[int]  # Step IDs that must complete first
    completed: bool
    result: Optional[Any]
    error: Optional[str]


class ConversationMessage(TypedDict):
    """A message in the conversation history."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]]


class AgentState(TypedDict):
    """
    Global state shared across all agents.
    This is the state that flows through the LangGraph.
    """
    # Input
    user_query: str
    conversation_history: Annotated[List[ConversationMessage], operator.add]
    
    # Intent Understanding
    detected_intent: Optional[QueryIntent]
    entities_mentioned: List[str]  # Companies, sectors, metrics mentioned
    ambiguities: List[str]  # Things that need clarification
    
    # Planning
    execution_plan: List[ExecutionStep]
    current_step_id: int
    
    # Data Retrieval
    sql_queries: Annotated[List[str], operator.add]
    query_results: Annotated[List[Dict[str, Any]], operator.add]
    
    # Analysis
    computed_metrics: Dict[str, Any]
    insights: Annotated[List[str], operator.add]
    
    # Visualization
    chart_config: Optional[Dict[str, Any]]
    chart_data: Optional[Any]
    
    # Response
    final_response: str
    response_metadata: Dict[str, Any]
    
    # Error Handling
    errors: Annotated[List[str], operator.add]
    retry_count: int
    
    # Evaluation
    evaluation_metrics: Dict[str, Any]


def create_initial_state(user_query: str) -> AgentState:
    """Create initial state for a new query."""
    return {
        "user_query": user_query,
        "conversation_history": [],
        "detected_intent": None,
        "entities_mentioned": [],
        "ambiguities": [],
        "execution_plan": [],
        "current_step_id": 0,
        "sql_queries": [],
        "query_results": [],
        "computed_metrics": {},
        "insights": [],
        "chart_config": None,
        "chart_data": None,
        "final_response": "",
        "response_metadata": {},
        "errors": [],
        "retry_count": 0,
        "evaluation_metrics": {}
    }


class ConversationMemory:
    """Manages conversation history and context."""
    
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.messages: List[ConversationMessage] = []
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to history."""
        from datetime import datetime
        
        message: ConversationMessage = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.messages.append(message)
        
        # Keep only recent history
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
    
    def get_context_for_llm(self, include_last_n: int = 5) -> str:
        """Format recent conversation history for LLM context."""
        recent = self.messages[-include_last_n:]
        context = "Previous conversation:\n"
        for msg in recent:
            context += f"{msg['role']}: {msg['content']}\n"
        return context
    
    def get_last_user_query(self) -> Optional[str]:
        """Get the most recent user query."""
        for msg in reversed(self.messages):
            if msg["role"] == "user":
                return msg["content"]
        return None
    
    def clear(self):
        """Clear conversation history."""
        self.messages = []