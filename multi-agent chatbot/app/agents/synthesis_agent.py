"""
Synthesis Agent - Combines results and generates final response.
"""
from typing import Dict, Any, List
import logging
from langchain_openai import ChatOpenAI
import pandas as pd

from app.agents.state import AgentState
from app.config import settings

logger = logging.getLogger(__name__)


class SynthesisAgent:
    """Agent responsible for synthesizing final responses."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            api_key=settings.openai_api_key
        )
    
    def synthesize_response(self, state: AgentState) -> AgentState:
        """
        Synthesize final response from all execution results.
        
        Args:
            state: Current agent state with execution results
            
        Returns:
            Updated state with final response
        """
        logger.info("Synthesis Agent: Creating final response")
        
        user_query = state["user_query"]
        query_results = state.get("query_results", [])
        computed_metrics = state.get("computed_metrics", {})
        errors = state.get("errors", [])
        ambiguities = state.get("ambiguities", [])
        
        # Handle clarification needed
        if ambiguities:
            response = self._generate_clarification_request(ambiguities)
            state["final_response"] = response
            return state
        
        # Handle errors
        if errors and not query_results:
            response = self._generate_error_response(errors)
            state["final_response"] = response
            return state
        
        # Generate response from results
        try:
            prompt = self._create_synthesis_prompt(
                user_query, query_results, computed_metrics
            )
            
            llm_response = self.llm.invoke(prompt)
            response = llm_response.content
            
            # Add metadata about data sources
            response_metadata = {
                "queries_executed": len(query_results),
                "rows_processed": sum(r.get("row_count", 0) for r in query_results),
                "has_visualization": state.get("chart_config") is not None
            }
            
            state["final_response"] = response
            state["response_metadata"] = response_metadata
            
            logger.info("Response synthesized successfully")
            
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            state["final_response"] = "I encountered an error generating the response. Please try rephrasing your question."
            state["errors"].append(f"Synthesis error: {str(e)}")
        
        return state
    
    def _create_synthesis_prompt(
        self, 
        user_query: str, 
        query_results: List[Dict], 
        computed_metrics: Dict
    ) -> str:
        """Create prompt for response synthesis."""
        
        # Format query results
        results_text = ""
        for i, result in enumerate(query_results, 1):
            results_text += f"\nQuery {i}:\n"
            results_text += f"SQL: {result.get('sql_query', 'N/A')}\n"
            
            df = pd.DataFrame(result.get("data", []))
            if len(df) > 0:
                # Show first few rows
                results_text += f"Results ({result.get('row_count', 0)} rows):\n"
                results_text += df.head(10).to_string() + "\n"
            else:
                results_text += "No results returned.\n"
        
        # Format computed metrics
        metrics_text = ""
        if computed_metrics:
            metrics_text = "\nComputed Metrics:\n"
            for key, value in computed_metrics.items():
                metrics_text += f"{key}: {value}\n"
        
        prompt = f"""You are a helpful assistant providing accurate answers about S&P 500 companies.

USER QUESTION: {user_query}

DATA RETRIEVED FROM DATABASE:
{results_text}

{metrics_text}

INSTRUCTIONS:
1. Answer the user's question DIRECTLY and ACCURATELY using ONLY the data provided above
2. Be conversational and natural in your response
3. If specific numbers are requested, include them clearly
4. If the data doesn't fully answer the question, acknowledge what's available
5. Do NOT make up or hallucinate any financial data
6. Do NOT speculate beyond what the data shows
7. Format numbers appropriately (e.g., "$2.8T" for market cap, "15.3%" for ratios)
8. If comparing multiple entities, present them clearly

Provide a clear, accurate response now:"""
        
        return prompt
    
    def _generate_clarification_request(self, ambiguities: List[str]) -> str:
        """Generate response requesting clarification."""
        response = "I need some clarification to answer your question accurately:\n\n"
        for i, ambiguity in enumerate(ambiguities, 1):
            response += f"{i}. {ambiguity}\n"
        response += "\nCould you provide more details?"
        return response
    
    def _generate_error_response(self, errors: List[str]) -> str:
        """Generate user-friendly error response."""
        return (
            "I encountered some difficulties processing your request. "
            "This might be because:\n"
            "- The information requested isn't available in the dataset\n"
            "- The query was too complex or ambiguous\n"
            "- There was a technical issue\n\n"
            "Could you try rephrasing your question or being more specific?"
        )