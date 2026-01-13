"""
Analysis Agent - Performs numerical analysis and calculations.
"""
from typing import Dict, Any, List
import logging
import pandas as pd
import numpy as np
from scipy import stats

from app.agents.state import AgentState, ExecutionStep

logger = logging.getLogger(__name__)


class AnalysisAgent:
    """Agent responsible for numerical analysis and calculations."""
    
    def execute_analysis_step(self, state: AgentState, step: ExecutionStep) -> AgentState:
        """
        Execute an analysis step.
        
        Args:
            state: Current agent state
            step: The analysis step to execute
            
        Returns:
            Updated state with analysis results
        """
        logger.info(f"Analysis Agent: Executing step {step['step_id']}")
        
        # Get data from previous steps
        query_results = state.get("query_results", [])
        if not query_results:
            step["error"] = "No data available for analysis"
            step["completed"] = True
            return state
        
        try:
            # Get the most recent query result
            latest_result = query_results[-1]
            df = pd.DataFrame(latest_result["data"])
            
            # Perform analysis based on step description
            analysis_type = self._determine_analysis_type(step["description"])
            
            if analysis_type == "statistics":
                result = self._compute_statistics(df)
            elif analysis_type == "comparison":
                result = self._perform_comparison(df)
            elif analysis_type == "correlation":
                result = self._compute_correlation(df)
            elif analysis_type == "ranking":
                result = self._perform_ranking(df)
            else:
                result = self._general_analysis(df)
            
            state["computed_metrics"].update(result)
            step["result"] = result
            step["completed"] = True
            
            logger.info(f"Analysis completed: {list(result.keys())}")
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            step["error"] = str(e)
            step["completed"] = True
            state["errors"].append(f"Analysis error: {str(e)}")
        
        return state
    
    def _determine_analysis_type(self, description: str) -> str:
        """Determine type of analysis from description."""
        desc_lower = description.lower()
        
        if any(word in desc_lower for word in ['average', 'mean', 'median', 'sum', 'total']):
            return "statistics"
        elif any(word in desc_lower for word in ['compare', 'comparison', 'versus', 'vs']):
            return "comparison"
        elif any(word in desc_lower for word in ['correlation', 'relationship']):
            return "correlation"
        elif any(word in desc_lower for word in ['rank', 'top', 'bottom', 'highest', 'lowest']):
            return "ranking"
        else:
            return "general"
    
    def _compute_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compute statistical measures."""
        result = {}
        
        for col in df.select_dtypes(include=[np.number]).columns:
            result[col] = {
                "count": int(df[col].count()),
                "mean": float(df[col].mean()) if not df[col].isna().all() else None,
                "median": float(df[col].median()) if not df[col].isna().all() else None,
                "std": float(df[col].std()) if not df[col].isna().all() else None,
                "min": float(df[col].min()) if not df[col].isna().all() else None,
                "max": float(df[col].max()) if not df[col].isna().all() else None,
                "sum": float(df[col].sum()) if not df[col].isna().all() else None
            }
        
        return result
    
    def _perform_comparison(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform comparison analysis."""
        result = {}
        
        # If there are exactly 2 rows, compare them
        if len(df) == 2:
            for col in df.select_dtypes(include=[np.number]).columns:
                val1, val2 = df[col].iloc[0], df[col].iloc[1]
                if pd.notna(val1) and pd.notna(val2):
                    diff = val2 - val1
                    pct_change = (diff / val1 * 100) if val1 != 0 else None
                    result[col] = {
                        "value_1": float(val1),
                        "value_2": float(val2),
                        "difference": float(diff),
                        "percent_change": float(pct_change) if pct_change is not None else None
                    }
        
        return result
    
    def _compute_correlation(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compute correlation between numerical columns."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) < 2:
            return {"error": "Need at least 2 numeric columns for correlation"}
        
        result = {}
        
        # Compute correlation matrix
        corr_matrix = df[numeric_cols].corr()
        
        # Get top correlations
        correlations = []
        for i, col1 in enumerate(numeric_cols):
            for j, col2 in enumerate(numeric_cols):
                if i < j:  # Avoid duplicates
                    corr_value = corr_matrix.iloc[i, j]
                    if pd.notna(corr_value):
                        correlations.append({
                            "column_1": col1,
                            "column_2": col2,
                            "correlation": float(corr_value)
                        })
        
        # Sort by absolute correlation
        correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)
        result["correlations"] = correlations[:5]  # Top 5
        
        return result
    
    def _perform_ranking(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform ranking analysis."""
        result = {}
        
        # Assume first numeric column is the ranking criterion
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            return {"error": "No numeric columns for ranking"}
        
        rank_col = numeric_cols[0]
        
        # Add rank
        df_sorted = df.sort_values(by=rank_col, ascending=False)
        result["ranked_data"] = df_sorted.to_dict('records')
        result["rank_column"] = rank_col
        
        return result
    
    def _general_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """General analysis summary."""
        return {
            "row_count": len(df),
            "column_count": len(df.columns),
            "numeric_columns": df.select_dtypes(include=[np.number]).columns.tolist(),
            "categorical_columns": df.select_dtypes(include=['object']).columns.tolist()
        }