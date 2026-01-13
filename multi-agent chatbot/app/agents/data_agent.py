"""
Data Retrieval Agent - Executes SQL queries against the database.
"""
from typing import Dict, Any
import logging
import pandas as pd

from app.agents.state import AgentState, ExecutionStep, AgentType
from app.database.manager import DatabaseManager
from app.database.metadata import DatabaseMetadataManager
from app.config import settings

logger = logging.getLogger(__name__)


class DataRetrievalAgent:
    """Agent responsible for data retrieval from database."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.metadata_manager = DatabaseMetadataManager()
    
    def execute_retrieval_step(self, state: AgentState, step: ExecutionStep) -> AgentState:
        """
        Execute a data retrieval step.
        
        Args:
            state: Current agent state
            step: The retrieval step to execute
            
        Returns:
            Updated state with query results
        """
        logger.info(f"Data Retrieval Agent: Executing step {step['step_id']}")
        
        # Get SQL query from step result or generate it
        sql_query = step.get("result")
        
        if not sql_query:
            logger.error("No SQL query provided in step")
            step["error"] = "No SQL query specified"
            step["completed"] = True
            state["errors"].append("Data retrieval failed: No SQL query")
            return state
        
        # Validate query against schema
        is_valid, error_msg = self._validate_query(sql_query)
        if not is_valid:
            logger.error(f"Query validation failed: {error_msg}")
            step["error"] = f"Invalid query: {error_msg}"
            step["completed"] = True
            state["errors"].append(f"Query validation failed: {error_msg}")
            return state
        
        try:
            # Execute query
            logger.info(f"Executing SQL: {sql_query}")
            result_df = self.db_manager.execute_query(sql_query)
            
            # Store results
            result_dict = {
                "step_id": step["step_id"],
                "sql_query": sql_query,
                "data": result_df.to_dict('records'),
                "row_count": len(result_df),
                "columns": result_df.columns.tolist()
            }
            
            state["sql_queries"].append(sql_query)
            state["query_results"].append(result_dict)
            
            step["result"] = result_dict
            step["completed"] = True
            
            logger.info(f"Query returned {len(result_df)} rows")
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            step["error"] = str(e)
            step["completed"] = True
            state["errors"].append(f"Query execution error: {str(e)}")
        
        return state
    
    def _validate_query(self, sql_query: str) -> tuple[bool, str]:
        """
        Validate SQL query against schema.
        
        Returns:
            (is_valid, error_message)
        """
        # Basic validation checks
        sql_lower = sql_query.lower()
        
        # Check for dangerous operations
        dangerous_keywords = ['drop', 'delete', 'truncate', 'insert', 'update', 'alter']
        for keyword in dangerous_keywords:
            if keyword in sql_lower:
                return False, f"Dangerous operation not allowed: {keyword}"
        
        # Check that it references the correct table
        if 'sp500_companies' not in sql_lower:
            return False, "Query must reference sp500_companies table"
        
        # Validate with database
        is_valid, error = self.db_manager.validate_query(sql_query)
        if not is_valid:
            return False, error
        
        return True, ""
    
    def get_sample_data(self, state: AgentState, limit: int = 5) -> AgentState:
        """Get sample data for exploration."""
        try:
            sample_df = self.db_manager.get_sample_data(limit)
            result_dict = {
                "step_id": 0,
                "sql_query": f"SELECT * FROM sp500_companies LIMIT {limit}",
                "data": sample_df.to_dict('records'),
                "row_count": len(sample_df),
                "columns": sample_df.columns.tolist()
            }
            state["query_results"].append(result_dict)
        except Exception as e:
            logger.error(f"Failed to get sample data: {e}")
            state["errors"].append(f"Sample data error: {str(e)}")
        
        return state