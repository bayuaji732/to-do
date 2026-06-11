"""
Multi-Agent Pipeline using LangGraph
Agents: Intent Analyst → Prompt Engineer → Knowledge Agent
Powered by OpenAI GPT-4.1 models
"""

import json
import os
import re
from typing import TypedDict, Optional, List, Dict, Any

from langgraph.graph import StateGraph, END
from openai import OpenAI


# ─────────────────────────────────────────────
# State Schema
# ─────────────────────────────────────────────
class AgentState(TypedDict):
    original_query: str
    model: str
    chat_history: List[Dict[str, Any]]   # [{"role": "user"|"assistant", "content": "..."}]

    # Outputs from each agent
    intent_analysis: Optional[Dict]      # {intent, category, clarity, missing, keywords}
    improved_prompt: Optional[Dict]      # {improved_prompt, changes, expected_quality_gain}
    final_response: Optional[str]

    # Control flags
    use_improved: bool                   # whether responder uses improved or original prompt
    error: Optional[str]


# ─────────────────────────────────────────────
# Helper: Call OpenAI
# ─────────────────────────────────────────────
def call_openai(
    user_content: str,
    system: str,
    model: str,
    history: Optional[List[Dict]] = None,
    max_tokens: int = 1500,
) -> str:
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    messages = [{"role": "system", "content": system}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_content})

    response = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=messages,
    )
    return response.choices[0].message.content


def parse_json_safe(text: str) -> Optional[Dict]:
    """Extract and parse JSON from model output."""
    try:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group())
    except (json.JSONDecodeError, AttributeError):
        pass
    return None


# ─────────────────────────────────────────────
# Agent System Prompts
# ─────────────────────────────────────────────
INTENT_SYSTEM = """You are an Intent Analyst AI. Analyze the user's query and return ONLY a JSON object:
{
  "intent": "1-line summary of what the user truly wants",
  "category": "one of: research | creative | technical | analysis | conversational | other",
  "clarity": "low | medium | high",
  "missing": ["list of missing context or specifics that would improve the answer"],
  "keywords": ["key concepts identified"]
}
Return ONLY valid JSON. No explanation, no markdown fences."""

IMPROVER_SYSTEM = """You are a world-class Prompt Engineer AI. Given the user's original query and its intent analysis, rewrite the prompt to be significantly more effective, specific, and well-scoped.

Return ONLY a JSON object:
{
  "improved_prompt": "the rewritten, enhanced version of the user's query",
  "changes": ["brief bullets of what you changed and why"],
  "expected_quality_gain": "short explanation of how this improves the response"
}
Return ONLY valid JSON. No explanation, no markdown fences."""

RESPONDER_SYSTEM = """You are an expert Knowledge Agent. You receive a well-crafted prompt and must provide the best possible response.
Be comprehensive, accurate, well-structured, and genuinely helpful. Use markdown formatting where appropriate.
If the conversation has prior history, maintain coherence with it."""


# ─────────────────────────────────────────────
# Agent Nodes
# ─────────────────────────────────────────────
def intent_agent(state: AgentState) -> AgentState:
    """Node 1 – Analyze the intent of the user's query."""
    try:
        raw = call_openai(
            user_content=state["original_query"],
            system=INTENT_SYSTEM,
            model=state["model"],
            max_tokens=600,
        )
        intent_data = parse_json_safe(raw)
        if not intent_data:
            intent_data = {
                "intent": state["original_query"],
                "category": "other",
                "clarity": "medium",
                "missing": [],
                "keywords": [],
            }
        return {**state, "intent_analysis": intent_data, "error": None}
    except Exception as e:
        return {**state, "error": f"Intent Agent error: {str(e)}"}


def prompt_improver_agent(state: AgentState) -> AgentState:
    """Node 2 – Rewrite the user's query into an optimized prompt."""
    if state.get("error"):
        return state
    try:
        content = (
            f"Original query: \"{state['original_query']}\"\n\n"
            f"Intent analysis:\n{json.dumps(state['intent_analysis'], indent=2)}"
        )
        raw = call_openai(
            user_content=content,
            system=IMPROVER_SYSTEM,
            model=state["model"],
            max_tokens=800,
        )
        improved_data = parse_json_safe(raw)
        if not improved_data:
            improved_data = {
                "improved_prompt": state["original_query"],
                "changes": ["No changes – original query was already clear."],
                "expected_quality_gain": "Minimal.",
            }
        return {**state, "improved_prompt": improved_data}
    except Exception as e:
        return {**state, "error": f"Prompt Improver error: {str(e)}"}


def knowledge_agent(state: AgentState) -> AgentState:
    """Node 3 – Generate the final response using the (optionally improved) prompt."""
    if state.get("error"):
        return state
    try:
        use_improved = state.get("use_improved", True)
        query = (
            state["improved_prompt"]["improved_prompt"]
            if use_improved and state.get("improved_prompt")
            else state["original_query"]
        )

        # Pass prior conversation history (excluding last user turn, already in query)
        history = state.get("chat_history", [])[:-1]  # all but the latest user message

        response = call_openai(
            user_content=query,
            system=RESPONDER_SYSTEM,
            model=state["model"],
            history=history if history else None,
            max_tokens=2000,
        )
        return {**state, "final_response": response}
    except Exception as e:
        return {**state, "error": f"Knowledge Agent error: {str(e)}"}


# ─────────────────────────────────────────────
# Build the LangGraph
# ─────────────────────────────────────────────
def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("intent_agent", intent_agent)
    graph.add_node("prompt_improver", prompt_improver_agent)
    graph.add_node("knowledge_agent", knowledge_agent)

    graph.set_entry_point("intent_agent")
    graph.add_edge("intent_agent", "prompt_improver")
    graph.add_edge("prompt_improver", "knowledge_agent")
    graph.add_edge("knowledge_agent", END)

    return graph.compile()


# Singleton compiled graph
PIPELINE = build_graph()


# ─────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────
def run_pipeline(
    query: str,
    model: str,
    chat_history: Optional[List[Dict]] = None,
    use_improved: bool = True,
) -> AgentState:
    """Run the full 3-agent pipeline and return the final state."""
    initial_state: AgentState = {
        "original_query": query,
        "model": model,
        "chat_history": chat_history or [],
        "intent_analysis": None,
        "improved_prompt": None,
        "final_response": None,
        "use_improved": use_improved,
        "error": None,
    }
    result = PIPELINE.invoke(initial_state)
    return result
