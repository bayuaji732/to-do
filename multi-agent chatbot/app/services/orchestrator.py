"""
Main orchestrator using LangGraph for multi-agent workflow.
"""
from typing import Dict, Any, Literal
import logging
from langgraph.graph import StateGraph, END

from app.agents.state import AgentState, AgentType, create_initial_state, ConversationMemory
from app.agents.intent_agent import IntentAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.data_agent import DataRetrievalAgent
from app.agents.analysis_agent import AnalysisAgent
from app.agents.visualization_agent import VisualizationAgent
from app.agents.synthesis_agent import SynthesisAgent
from app.database.manager import DatabaseManager
from app.config import settings

logger = logging.getLogger(__name__)


class MultiAgentOrchestrator:
    """Orchestrates the multi-agent system using LangGraph."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.conversation_memory = ConversationMemory()
        
        # Initialize agents
        self.intent_agent = IntentAgent()
        self.planner_agent = PlannerAgent()
        self.data_agent = DataRetrievalAgent(db_manager)
        self.analysis_agent = AnalysisAgent()
        self.viz_agent = VisualizationAgent()
        self.synthesis_agent = SynthesisAgent()
        
        # Build workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("intent", self._intent_node)
        workflow.add_node("planner", self._planner_node)
        workflow.add_node("executor", self._executor_node)
        workflow.add_node("synthesis", self._synthesis_node)
        
        # Define edges
        workflow.set_entry_point("intent")
        workflow.add_edge("intent", "planner")
        workflow.add_edge("planner", "executor")
        workflow.add_edge("executor", "synthesis")
        workflow.add_edge("synthesis", END)
        
        return workflow.compile()
    
    def _intent_node(self, state: AgentState) -> AgentState:
        """Intent understanding node."""
        logger.info("=== Intent Node ===")
        return self.intent_agent.analyze_intent(state)
    
    def _planner_node(self, state: AgentState) -> AgentState:
        """Planning node."""
        logger.info("=== Planner Node ===")
        return self.planner_agent.create_plan(state)
    
    def _executor_node(self, state: AgentState) -> AgentState:
        """Execution node - processes all steps in the plan."""
        logger.info("=== Executor Node ===")
        
        execution_plan = state.get("execution_plan", [])
        
        for step in execution_plan:
            if step["completed"]:
                continue
            
            # Check dependencies
            dependencies = step.get("dependencies", [])
            if not self._dependencies_met(execution_plan, dependencies):
                logger.warning(f"Step {step['step_id']} dependencies not met")
                continue
            
            # Execute based on agent type
            agent_type = step["agent_type"]
            
            try:
                if agent_type == AgentType.DATA_RETRIEVAL:
                    state = self.data_agent.execute_retrieval_step(state, step)
                elif agent_type == AgentType.ANALYSIS:
                    state = self.analysis_agent.execute_analysis_step(state, step)
                elif agent_type == AgentType.VISUALIZATION:
                    state = self.viz_agent.execute_visualization_step(state, step)
                else:
                    # Skip other agent types in executor
                    step["completed"] = True
                    
            except Exception as e:
                logger.error(f"Step {step['step_id']} failed: {e}")
                step["error"] = str(e)
                step["completed"] = True
                state["errors"].append(f"Step {step['step_id']} error: {str(e)}")
        
        return state
    
    def _synthesis_node(self, state: AgentState) -> AgentState:
        """Synthesis node."""
        logger.info("=== Synthesis Node ===")
        return self.synthesis_agent.synthesize_response(state)
    
    def _dependencies_met(self, plan: list, dependency_ids: list) -> bool:
        """Check if all dependencies are completed."""
        if not dependency_ids:
            return True
        
        for step in plan:
            if step["step_id"] in dependency_ids:
                if not step["completed"] or step.get("error"):
                    return False
        
        return True
    
    def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        Process a user query through the multi-agent system.
        
        Args:
            user_query: The user's question
            
        Returns:
            Dict containing response and metadata
        """
        logger.info(f"Processing query: {user_query}")
        
        # Create initial state
        state = create_initial_state(user_query)
        
        # Add conversation history
        state["conversation_history"] = self.conversation_memory.messages.copy()
        
        try:
            # Run workflow
            final_state = self.workflow.invoke(state)
            
            # Extract response
            response = {
                "response": final_state.get("final_response", "I couldn't generate a response."),
                "metadata": final_state.get("response_metadata", {}),
                "chart_config": final_state.get("chart_config"),
                "query_results": final_state.get("query_results", []),
                "errors": final_state.get("errors", []),
                "detected_intent": final_state.get("detected_intent", {}).value if final_state.get("detected_intent") else None
            }
            
            # Update conversation memory
            self.conversation_memory.add_message("user", user_query)
            self.conversation_memory.add_message(
                "assistant", 
                response["response"],
                metadata=response["metadata"]
            )
            
            logger.info("Query processed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            return {
                "response": f"An error occurred: {str(e)}",
                "metadata": {},
                "chart_config": None,
                "query_results": [],
                "errors": [str(e)],
                "detected_intent": None
            }
    
    def reset_conversation(self):
        """Reset conversation memory."""
        self.conversation_memory.clear()
        logger.info("Conversation reset")