"""
Visualization Agent - Creates charts and visualizations.
"""
from typing import Dict, Any, Optional
import logging
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from app.agents.state import AgentState, ExecutionStep

logger = logging.getLogger(__name__)


class VisualizationAgent:
    """Agent responsible for creating visualizations."""
    
    def execute_visualization_step(self, state: AgentState, step: ExecutionStep) -> AgentState:
        """
        Execute a visualization step.
        
        Args:
            state: Current agent state
            step: The visualization step to execute
            
        Returns:
            Updated state with chart configuration
        """
        logger.info(f"Visualization Agent: Executing step {step['step_id']}")
        
        # Get data from query results
        query_results = state.get("query_results", [])
        if not query_results:
            step["error"] = "No data available for visualization"
            step["completed"] = True
            return state
        
        try:
            # Get the most recent query result
            latest_result = query_results[-1]
            df = pd.DataFrame(latest_result["data"])
            
            # Determine chart type
            chart_type = self._determine_chart_type(df, step["description"])
            
            # Create visualization
            fig = self._create_chart(df, chart_type, step["description"])
            
            if fig:
                # Convert to JSON for storage/transmission
                chart_config = {
                    "type": chart_type,
                    "data": fig.to_json(),
                    "html": fig.to_html(include_plotlyjs='cdn')
                }
                
                state["chart_config"] = chart_config
                state["chart_data"] = df.to_dict('records')
                step["result"] = chart_config
                
                logger.info(f"Created {chart_type} visualization")
            
            step["completed"] = True
            
        except Exception as e:
            logger.error(f"Visualization failed: {e}")
            step["error"] = str(e)
            step["completed"] = True
            state["errors"].append(f"Visualization error: {str(e)}")
        
        return state
    
    def _determine_chart_type(self, df: pd.DataFrame, description: str) -> str:
        """Determine appropriate chart type."""
        desc_lower = description.lower()
        
        # Explicit chart type requests
        if 'bar' in desc_lower:
            return 'bar'
        elif 'line' in desc_lower:
            return 'line'
        elif 'pie' in desc_lower:
            return 'pie'
        elif 'scatter' in desc_lower:
            return 'scatter'
        elif 'histogram' in desc_lower:
            return 'histogram'
        
        # Infer from data
        numeric_cols = df.select_dtypes(include=['number']).columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        
        # Single categorical, single numeric -> bar chart
        if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
            return 'bar'
        
        # Multiple numeric columns -> line or scatter
        elif len(numeric_cols) >= 2:
            return 'scatter'
        
        # Single numeric -> histogram
        elif len(numeric_cols) == 1:
            return 'histogram'
        
        return 'table'
    
    def _create_chart(self, df: pd.DataFrame, chart_type: str, description: str) -> Optional[go.Figure]:
        """Create a Plotly chart based on type."""
        
        if len(df) == 0:
            logger.warning("Empty dataframe, cannot create chart")
            return None
        
        try:
            if chart_type == 'bar':
                return self._create_bar_chart(df)
            elif chart_type == 'line':
                return self._create_line_chart(df)
            elif chart_type == 'pie':
                return self._create_pie_chart(df)
            elif chart_type == 'scatter':
                return self._create_scatter_chart(df)
            elif chart_type == 'histogram':
                return self._create_histogram(df)
            else:
                return None
        except Exception as e:
            logger.error(f"Chart creation failed: {e}")
            return None
    
    def _create_bar_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create bar chart."""
        # Get first categorical and first numeric column
        cat_cols = df.select_dtypes(include=['object']).columns
        num_cols = df.select_dtypes(include=['number']).columns
        
        if len(cat_cols) == 0 or len(num_cols) == 0:
            raise ValueError("Need categorical and numeric columns for bar chart")
        
        x_col = cat_cols[0]
        y_col = num_cols[0]
        
        fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}")
        fig.update_layout(height=500, template="plotly_white")
        
        return fig
    
    def _create_line_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create line chart."""
        # Assume first column is x-axis, others are y-axis
        x_col = df.columns[0]
        y_cols = df.select_dtypes(include=['number']).columns
        
        fig = go.Figure()
        for col in y_cols:
            fig.add_trace(go.Scatter(x=df[x_col], y=df[col], mode='lines+markers', name=col))
        
        fig.update_layout(
            title="Time Series",
            xaxis_title=x_col,
            yaxis_title="Value",
            height=500,
            template="plotly_white"
        )
        
        return fig
    
    def _create_pie_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create pie chart."""
        cat_cols = df.select_dtypes(include=['object']).columns
        num_cols = df.select_dtypes(include=['number']).columns
        
        if len(cat_cols) == 0 or len(num_cols) == 0:
            raise ValueError("Need categorical and numeric columns for pie chart")
        
        labels_col = cat_cols[0]
        values_col = num_cols[0]
        
        fig = px.pie(df, names=labels_col, values=values_col, title=f"{values_col} Distribution")
        fig.update_layout(height=500)
        
        return fig
    
    def _create_scatter_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create scatter plot."""
        num_cols = df.select_dtypes(include=['number']).columns
        
        if len(num_cols) < 2:
            raise ValueError("Need at least 2 numeric columns for scatter plot")
        
        x_col = num_cols[0]
        y_col = num_cols[1]
        
        # Check if there's a categorical column for coloring
        cat_cols = df.select_dtypes(include=['object']).columns
        color_col = cat_cols[0] if len(cat_cols) > 0 else None
        
        fig = px.scatter(
            df, 
            x=x_col, 
            y=y_col, 
            color=color_col,
            title=f"{y_col} vs {x_col}"
        )
        fig.update_layout(height=500, template="plotly_white")
        
        return fig
    
    def _create_histogram(self, df: pd.DataFrame) -> go.Figure:
        """Create histogram."""
        num_cols = df.select_dtypes(include=['number']).columns
        
        if len(num_cols) == 0:
            raise ValueError("Need numeric column for histogram")
        
        col = num_cols[0]
        
        fig = px.histogram(df, x=col, title=f"Distribution of {col}")
        fig.update_layout(height=500, template="plotly_white")
        
        return fig