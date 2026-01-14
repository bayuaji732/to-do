"""
Streamlit frontend for the S&P 500 Multi-Agent Chatbot.
"""
import streamlit as st
import requests
import json
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Any

# Configuration
API_URL = "http://localhost:8000"

# Page config
st.set_page_config(
    page_title="S&P 500 AI Assistant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
    }
    .assistant-message {
        background-color: #f5f5f5;
    }
</style>
""", unsafe_allow_html=True)


def check_api_health() -> bool:
    """Check if API is running."""
    try:
        response = requests.get(f"{API_URL}/")
        return response.status_code == 200
    except:
        return False


def send_query(query: str) -> Dict[str, Any]:
    """Send query to API."""
    try:
        response = requests.post(
            f"{API_URL}/query",
            json={"query": query}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None


def reset_conversation():
    """Reset conversation history."""
    try:
        requests.post(f"{API_URL}/reset")
        st.session_state.messages = []
    except Exception as e:
        st.error(f"Error resetting conversation: {str(e)}")


def get_schema() -> Dict[str, Any]:
    """Get database schema."""
    try:
        response = requests.get(f"{API_URL}/schema")
        return response.json()
    except:
        return None


def get_sample_data() -> pd.DataFrame:
    """Get sample data."""
    try:
        response = requests.get(f"{API_URL}/sample-data?limit=5")
        data = response.json()
        return pd.DataFrame(data["data"])
    except:
        return None


def display_chart(chart_config: Dict):
    """Display Plotly chart."""
    try:
        fig = go.Figure(json.loads(chart_config["data"]))
        st.plotly_chart(fig, width="stretch")
    except Exception as e:
        st.error(f"Could not display chart: {str(e)}")


def display_query_results(results: list):
    """Display query results as tables."""
    for i, result in enumerate(results):
        with st.expander(f"Query {i+1}: {result['row_count']} rows"):
            st.code(result["sql_query"], language="sql")
            if result["data"]:
                df = pd.DataFrame(result["data"])
                st.dataframe(df, width="stretch")


# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar
with st.sidebar:
    st.title("📊 S&P 500 AI Assistant")
    
    st.markdown("---")
    
    # API Status
    api_healthy = check_api_health()
    if api_healthy:
        st.success("✅ API Connected")
    else:
        st.error("❌ API Disconnected")
        st.warning("Please start the API server with: `python -m api.main`")
    
    st.markdown("---")
    
    # Actions
    st.subheader("Actions")
    if st.button("🔄 Reset Conversation"):
        reset_conversation()
        st.rerun()
    
    if st.button("📥 View Sample Data"):
        st.session_state.show_sample = True
    
    if st.button("📋 View Schema"):
        st.session_state.show_schema = True
    
    st.markdown("---")
    
    # Example queries
    st.subheader("Example Queries")
    example_queries = [
        "What is Apple's market cap?",
        "Compare revenue of Apple and Microsoft",
        "Top 5 companies by revenue",
        "Average PE ratio in tech sector",
        "Companies with market cap over 1 trillion",
        "Show me a chart of top 10 companies by employees"
    ]
    
    for query in example_queries:
        if st.button(query, key=f"example_{query}"):
            st.session_state.example_query = query

# Main content
st.title("💬 Chat with S&P 500 Data")

# Display sample data if requested
if st.session_state.get("show_sample"):
    with st.expander("📊 Sample Data", expanded=True):
        sample_df = get_sample_data()
        if sample_df is not None:
            st.dataframe(sample_df, width="stretch")
        st.session_state.show_sample = False

# Display schema if requested
if st.session_state.get("show_schema"):
    with st.expander("📋 Database Schema", expanded=True):
        schema_info = get_schema()
        if schema_info:
            st.text(schema_info["schema"])
        st.session_state.show_schema = False

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Display metadata if available
        if "metadata" in message and message["metadata"]:
            meta = message["metadata"]
            if meta.get("has_visualization"):
                st.info("📊 Visualization included")
        
        # Display chart if available
        if "chart" in message and message["chart"]:
            display_chart(message["chart"])
        
        # Display query results if available
        if "query_results" in message and message["query_results"]:
            with st.expander("View Query Details"):
                display_query_results(message["query_results"])

# Handle example query
if st.session_state.get("example_query"):
    user_input = st.session_state.example_query
    st.session_state.example_query = None
else:
    # Chat input
    user_input = st.chat_input("Ask a question about S&P 500 companies...")

if user_input:
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Add to message history
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })
    
    # Get response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = send_query(user_input)
        
        if response:
            st.markdown(response["response"])
            
            # Store assistant message
            assistant_message = {
                "role": "assistant",
                "content": response["response"],
                "metadata": response.get("metadata", {}),
                "chart": response.get("chart_config"),
                "query_results": response.get("query_results", [])
            }
            st.session_state.messages.append(assistant_message)
            
            # Display visualization if present
            if response.get("chart_config"):
                display_chart(response["chart_config"])
            
            # Display query details in expander
            if response.get("query_results"):
                with st.expander("View Query Details"):
                    display_query_results(response["query_results"])
            
            # Display errors if any
            if response.get("errors"):
                with st.expander("⚠️ Warnings", expanded=False):
                    for error in response["errors"]:
                        st.warning(error)
            
            # Display metadata
            if response.get("metadata"):
                meta = response["metadata"]
                cols = st.columns(3)
                with cols[0]:
                    st.metric("Queries", meta.get("queries_executed", 0))
                with cols[1]:
                    st.metric("Rows", meta.get("rows_processed", 0))
                with cols[2]:
                    intent = response.get("detected_intent", "Unknown")
                    st.metric("Intent", intent)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "Multi-Agent GenAI System | Powered by OpenAI & LangGraph"
    "</div>",
    unsafe_allow_html=True
)