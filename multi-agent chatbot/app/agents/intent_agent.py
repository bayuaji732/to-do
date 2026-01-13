"""
Intent Understanding Agent - Analyzes user queries to understand intent.
"""
from typing import Dict, Any, List
import json
import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.agents.state import AgentState, QueryIntent
from app.database.metadata import DatabaseMetadataManager
from app.config import settings

logger = logging.getLogger(__name__)


class IntentAgent:
    """Agent responsible for understanding user intent and extracting entities."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            api_key=settings.openai_api_key
        )
        self.metadata_manager = DatabaseMetadataManager()
    
    def analyze_intent(self, state: AgentState) -> AgentState:
        """
        Analyze user query to determine intent and extract entities.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with intent and entities
        """
        logger.info("Intent Agent: Analyzing user query")
        
        user_query = state["user_query"]
        conversation_history = state.get("conversation_history", [])
        
        # Build context from conversation history
        context = ""
        if conversation_history:
            context = "Previous conversation:\n"
            for msg in conversation_history[-3:]:  # Last 3 messages
                context += f"{msg['role']}: {msg['content']}\n"
        
        # Create prompt for intent analysis
        prompt = self._create_intent_prompt(user_query, context)
        
        try:
            # Get LLM response
            response = self.llm.invoke(prompt)
            result = self._parse_intent_response(response.content)
            
            # Update state
            state["detected_intent"] = result["intent"]
            state["entities_mentioned"] = result["entities"]
            state["ambiguities"] = result["ambiguities"]
            
            logger.info(f"Detected intent: {result['intent']}")
            logger.info(f"Entities: {result['entities']}")
            
        except Exception as e:
            logger.error(f"Intent analysis failed: {e}")
            state["errors"].append(f"Intent analysis error: {str(e)}")
            state["detected_intent"] = QueryIntent.UNCLEAR
        
        return state
    
    def _create_intent_prompt(self, user_query: str, context: str) -> str:
        """Create prompt for intent analysis."""
        schema = self.metadata_manager.get_schema_description()
        
        prompt = f"""You are an expert at understanding user queries about S&P 500 companies.

DATABASE SCHEMA:
{schema}

{context}

CURRENT USER QUERY: {user_query}

Analyze this query and provide a JSON response with:
1. intent: The primary intent (choose one):
   - lookup: Simple data retrieval (e.g., "What is Apple's market cap?")
   - comparison: Comparing entities (e.g., "Compare revenue of Apple and Microsoft")
   - aggregation: Sum, average, count (e.g., "What's the average PE ratio in tech sector?")
   - ranking: Top N or bottom N (e.g., "Top 10 companies by revenue")
   - trend: Time-based analysis (e.g., "How has revenue changed?")
   - correlation: Relationship analysis (e.g., "Is there correlation between PE ratio and dividend yield?")
   - filter: Filtering based on conditions (e.g., "Companies with revenue > 100B")
   - visualization: Explicit chart request (e.g., "Show me a chart of...")
   - unclear: Ambiguous or unclear intent

2. entities: List of specific entities mentioned (company names, sectors, metrics)
   - ONLY include entities that exist in the schema
   - Use exact column names from the schema
   - Include company symbols if mentioned (e.g., ["AAPL", "MSFT"])
   - Include sectors if mentioned (e.g., ["Information Technology"])
   - Include metrics if mentioned (e.g., ["Market_Cap", "Revenue"])

3. ambiguities: List of unclear aspects that may need clarification
   - Missing information needed to answer the query
   - Ambiguous references (e.g., "last year" when no date context exists)
   - Unclear entity references

4. requires_context: Boolean indicating if query depends on conversation context

RESPOND ONLY WITH VALID JSON:
{{
  "intent": "lookup|comparison|aggregation|ranking|trend|correlation|filter|visualization|unclear",
  "entities": ["entity1", "entity2"],
  "ambiguities": ["ambiguity1"],
  "requires_context": true/false
}}"""
        
        return prompt
    
    def _parse_intent_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured format."""
        try:
            # Extract JSON from response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            
            result = json.loads(response.strip())
            
            # Convert intent string to enum
            intent_str = result.get("intent", "unclear")
            try:
                intent = QueryIntent(intent_str)
            except ValueError:
                intent = QueryIntent.UNCLEAR
            
            return {
                "intent": intent,
                "entities": result.get("entities", []),
                "ambiguities": result.get("ambiguities", []),
                "requires_context": result.get("requires_context", False)
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse intent response: {e}")
            return {
                "intent": QueryIntent.UNCLEAR,
                "entities": [],
                "ambiguities": ["Failed to understand query"],
                "requires_context": False
            }