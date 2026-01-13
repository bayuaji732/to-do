"""
Planning Agent - Creates execution plans for queries.
"""
from typing import List, Dict, Any
import json
import logging
from langchain_openai import ChatOpenAI

from app.agents.state import AgentState, QueryIntent, AgentType, ExecutionStep
from app.database.metadata import DatabaseMetadataManager
from app.config import settings

logger = logging.getLogger(__name__)


class PlannerAgent:
    """Agent responsible for creating execution plans."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            api_key=settings.openai_api_key
        )
        self.metadata_manager = DatabaseMetadataManager()
    
    def create_plan(self, state: AgentState) -> AgentState:
        """
        Create an execution plan based on detected intent.
        
        Args:
            state: Current agent state with detected intent
            
        Returns:
            Updated state with execution plan
        """
        logger.info("Planner Agent: Creating execution plan")
        
        intent = state["detected_intent"]
        entities = state["entities_mentioned"]
        ambiguities = state["ambiguities"]
        
        # Handle ambiguous queries
        if intent == QueryIntent.UNCLEAR or ambiguities:
            state["execution_plan"] = self._create_clarification_plan(ambiguities)
            return state
        
        # Create plan based on intent
        prompt = self._create_planning_prompt(state)
        
        try:
            response = self.llm.invoke(prompt)
            execution_plan = self._parse_plan_response(response.content)
            state["execution_plan"] = execution_plan
            
            logger.info(f"Created plan with {len(execution_plan)} steps")
            for step in execution_plan:
                logger.info(f"  Step {step['step_id']}: {step['description']}")
                
        except Exception as e:
            logger.error(f"Planning failed: {e}")
            state["errors"].append(f"Planning error: {str(e)}")
            state["execution_plan"] = self._create_fallback_plan()
        
        return state
    
    def _create_planning_prompt(self, state: AgentState) -> str:
        """Create prompt for execution planning."""
        schema = self.metadata_manager.get_schema_description()
        
        intent = state["detected_intent"]
        entities = state["entities_mentioned"]
        user_query = state["user_query"]
        
        prompt = f"""You are an expert at creating execution plans for data queries.

DATABASE SCHEMA:
{schema}

USER QUERY: {user_query}
DETECTED INTENT: {intent.value if intent else 'unclear'}
ENTITIES MENTIONED: {', '.join(entities) if entities else 'none'}

Create a step-by-step execution plan to answer this query. Each step should be one of:
- DATA_RETRIEVAL: Execute SQL query to get data
- ANALYSIS: Perform calculations or statistical analysis
- VISUALIZATION: Create charts or graphs
- SYNTHESIS: Combine results and generate response

IMPORTANT RULES:
1. Each step must have a clear, specific description
2. Steps must be executed in logical order (dependencies)
3. SQL queries must only use columns from the schema above
4. All calculations must be explicit (no hallucinated math)
5. Include visualization step if intent is visualization or if data benefits from visual representation

RESPOND WITH VALID JSON ARRAY:
[
  {{
    "step_id": 1,
    "agent_type": "data_retrieval",
    "description": "Query to get Apple's market cap from sp500_companies table",
    "dependencies": [],
    "sql_query": "SELECT Security, Market_Cap FROM sp500_companies WHERE Symbol = 'AAPL'"
  }},
  {{
    "step_id": 2,
    "agent_type": "synthesis",
    "description": "Format and present the market cap value",
    "dependencies": [1]
  }}
]

Generate the execution plan now:"""
        
        return prompt
    
    def _parse_plan_response(self, response: str) -> List[ExecutionStep]:
        """Parse LLM response into execution steps."""
        try:
            # Clean response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            
            steps_data = json.loads(response.strip())
            
            execution_plan = []
            for step_data in steps_data:
                # Convert agent_type string to enum
                agent_type_str = step_data.get("agent_type", "").upper()
                try:
                    agent_type = AgentType[agent_type_str]
                except KeyError:
                    agent_type = AgentType.DATA_RETRIEVAL
                
                step: ExecutionStep = {
                    "step_id": step_data.get("step_id", len(execution_plan) + 1),
                    "agent_type": agent_type,
                    "description": step_data.get("description", ""),
                    "dependencies": step_data.get("dependencies", []),
                    "completed": False,
                    "result": step_data.get("sql_query"),  # Store SQL if provided
                    "error": None
                }
                execution_plan.append(step)
            
            return execution_plan
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse plan response: {e}")
            return self._create_fallback_plan()
    
    def _create_clarification_plan(self, ambiguities: List[str]) -> List[ExecutionStep]:
        """Create plan that asks for clarification."""
        step: ExecutionStep = {
            "step_id": 1,
            "agent_type": AgentType.SYNTHESIS,
            "description": f"Request clarification: {', '.join(ambiguities)}",
            "dependencies": [],
            "completed": False,
            "result": None,
            "error": None
        }
        return [step]
    
    def _create_fallback_plan(self) -> List[ExecutionStep]:
        """Create a simple fallback plan."""
        return [
            {
                "step_id": 1,
                "agent_type": AgentType.SYNTHESIS,
                "description": "Provide basic response",
                "dependencies": [],
                "completed": False,
                "result": None,
                "error": None
            }
        ]