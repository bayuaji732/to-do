# ◈◉◆ Multi-Agent Query Intelligence

A Python + LangGraph + Streamlit chatbot that runs every user query through a 3-agent pipeline before answering.

## Architecture

```
User Query
    │
    ▼
◈ Intent Analyst        — Decodes what the user truly wants
    │                     Returns: intent, category, clarity, missing context, keywords
    ▼
◉ Prompt Engineer       — Rewrites the query into an optimized prompt
    │                     Returns: improved_prompt, changes, expected_quality_gain
    ▼
◆ Knowledge Agent       — Generates a high-quality response
    │                     Uses either the improved prompt OR original query (toggle)
    ▼
  Response
```

## Quick Start

### 1. Clone / download files
```
multi_agent_chatbot/
├── app.py              ← Streamlit UI
├── agents.py           ← LangGraph pipeline
├── requirements.txt
├── .env.example
└── README.md
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up API key
```bash
cp .env.example .env
# Open .env and paste your Anthropic API key
```

### 5. Run the app
```bash
streamlit run app.py
```
Then open **http://localhost:8501** in your browser.

---

## Features

| Feature | Details |
|---|---|
| **3-Agent Pipeline** | Intent Analyst → Prompt Engineer → Knowledge Agent |
| **Model Selector** | Switch between Haiku, Sonnet, Opus from the sidebar |
| **Chat History** | Full conversation memory passed to agents for context |
| **Improved Prompt Toggle** | Choose whether to use the optimized prompt or original |
| **Copy Buttons** | Copy optimized prompt or final response with one click |
| **Export** | Download conversation as JSON or Markdown |
| **Clear Chat** | Reset the conversation anytime |

## Files

### `agents.py`
- `AgentState` — TypedDict that flows through the LangGraph graph
- `intent_agent` — Node 1: analyzes query intent, returns structured JSON
- `prompt_improver_agent` — Node 2: rewrites query into optimized prompt
- `knowledge_agent` — Node 3: generates final answer using (improved) prompt
- `build_graph()` — Compiles the LangGraph StateGraph
- `run_pipeline()` — Public function to invoke the full pipeline

### `app.py`
- Streamlit UI with sidebar controls
- Renders each agent's output in expandable sections
- Handles copy-to-clipboard, export, and chat history display

## Customization

**Add more agents:** Edit `agents.py`, add a new node function and wire it into the graph with `graph.add_node()` and `graph.add_edge()`.

**Change models:** Edit `AVAILABLE_MODELS` dict in `app.py`.

**Adjust pipeline:** Set `use_improved=False` in `run_pipeline()` to always use the original query.
