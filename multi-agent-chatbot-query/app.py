"""
Multi-Agent Query Intelligence — Streamlit App
Features: chat history, model selector, copy buttons, export conversation
"""

import json
import os
import time
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

from agents import run_pipeline

# ─────────────────────────────────────────────
# Config & Init
# ─────────────────────────────────────────────
load_dotenv()

st.set_page_config(
    page_title="Multi-Agent Query Intelligence",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

AVAILABLE_MODELS = {
    "GPT-4.1 nano  (fastest · cheapest)": "gpt-4.1-nano",
    "GPT-4.1 mini  (balanced · recommended)": "gpt-4.1-mini",
    "GPT-4o mini  (alternative fast)": "gpt-4o-mini",
}

CATEGORY_COLORS = {
    "research":       "#64B5F6",
    "creative":       "#F48FB1",
    "technical":      "#81C784",
    "analysis":       "#FFD54F",
    "conversational": "#CE93D8",
    "other":          "#90A4AE",
}

CLARITY_COLORS = {
    "low":    "#EF5350",
    "medium": "#FFA726",
    "high":   "#66BB6A",
}


# ─────────────────────────────────────────────
# Session State Bootstrap
# ─────────────────────────────────────────────
def init_session():
    defaults = {
        "messages":       [],   # [{role, content, intent, improved, response, model, ts}]
        "processing":     False,
        "selected_model": list(AVAILABLE_MODELS.keys())[1],
        "use_improved":   True,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_session()


# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Crimson+Pro:wght@300;400;600&display=swap');

html, body, [class*="css"] { font-family: 'DM Mono', monospace; }

.main-title {
    font-family: 'Crimson Pro', serif;
    font-size: 2rem;
    font-weight: 600;
    color: #e8e8e8;
    margin-bottom: 0;
}
.subtitle {
    color: #3a6a8a;
    font-size: 0.75rem;
    letter-spacing: 3px;
    margin-bottom: 1.5rem;
}
.agent-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.72rem;
    font-family: 'DM Mono', monospace;
    letter-spacing: 1px;
    margin-right: 6px;
    margin-bottom: 4px;
}
.intent-box {
    background: #0e1621;
    border: 1px solid #1e2d3d;
    border-left: 3px solid #64B5F6;
    border-radius: 8px;
    padding: 12px;
    margin-top: 8px;
    font-size: 0.82rem;
}
.improved-box {
    background: #0a1a12;
    border: 1px solid #1a3025;
    border-left: 3px solid #81C784;
    border-radius: 8px;
    padding: 12px;
    margin-top: 8px;
    font-size: 0.82rem;
}
.response-box {
    background: #0d0d1a;
    border: 1px solid #1e1e3a;
    border-left: 3px solid #CE93D8;
    border-radius: 8px;
    padding: 14px;
    margin-top: 8px;
    font-size: 0.85rem;
}
.user-msg {
    background: #0d2137;
    border: 1px solid #1e3f5e;
    border-radius: 12px 4px 12px 12px;
    padding: 12px 16px;
    margin-bottom: 8px;
    font-size: 0.88rem;
    color: #e0e0e0;
}
.tag {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.7rem;
    margin-right: 4px;
    background: #1a2535;
}
.section-label {
    font-size: 0.65rem;
    letter-spacing: 2px;
    margin-bottom: 6px;
    font-family: 'DM Mono', monospace;
}
.timestamp {
    font-size: 0.62rem;
    color: #3a4a5a;
    float: right;
}
.stButton > button {
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    letter-spacing: 1px;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ◈ Control Panel")
    st.markdown("---")

    # API Key status
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if api_key:
        st.success("✓ API Key loaded from .env")
    else:
        st.error("✗ OPENAI_API_KEY not found in .env")
        st.info("Add your key to `.env`:\n```\nOPENAI_API_KEY=sk-...\n```")

    st.markdown("---")

    # Model selector
    st.markdown("#### ◉ Model")
    selected_label = st.selectbox(
        "Choose model:",
        options=list(AVAILABLE_MODELS.keys()),
        index=list(AVAILABLE_MODELS.keys()).index(st.session_state.selected_model),
        label_visibility="collapsed",
    )
    st.session_state.selected_model = selected_label
    model_id = AVAILABLE_MODELS[selected_label]
    st.caption(f"`{model_id}`")

    st.markdown("---")

    # Pipeline settings
    st.markdown("#### ◆ Pipeline Settings")
    st.session_state.use_improved = st.toggle(
        "Use improved prompt for response",
        value=st.session_state.use_improved,
        help="When ON, the Knowledge Agent uses the Prompt Engineer's rewrite. When OFF, it uses your original query.",
    )

    st.markdown("---")

    # Export
    st.markdown("#### ▷ Export Conversation")
    if st.session_state.messages:
        col1, col2 = st.columns(2)

        with col1:
            # Export as JSON
            export_data = {
                "exported_at": datetime.now().isoformat(),
                "model": model_id,
                "conversation": st.session_state.messages,
            }
            st.download_button(
                label="⬇ JSON",
                data=json.dumps(export_data, indent=2, ensure_ascii=False),
                file_name=f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True,
            )

        with col2:
            # Export as Markdown
            md_lines = [
                "# Multi-Agent Chat Export",
                f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                f"**Model:** `{model_id}`",
                "---",
            ]
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    md_lines.append(f"\n## 🧑 User\n{msg['content']}")
                    if msg.get("intent"):
                        intent = msg["intent"]
                        md_lines.append(f"\n**Intent:** {intent.get('intent','')}")
                    if msg.get("improved"):
                        imp = msg["improved"]
                        md_lines.append(f"\n**Optimized Prompt:** _{imp.get('improved_prompt','')}_")
                    if msg.get("response"):
                        md_lines.append(f"\n## 🤖 Agent\n{msg['response']}")
                    md_lines.append("\n---")

            st.download_button(
                label="⬇ MD",
                data="\n".join(md_lines),
                file_name=f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                use_container_width=True,
            )

        st.markdown("---")

        if st.button("🗑 Clear Conversation", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    else:
        st.caption("No conversation yet.")

    st.markdown("---")
    st.markdown("##### Pipeline")
    st.markdown("""
    <div style='font-size:0.72rem; line-height:2; color:#4a6a7a;'>
    <span style='color:#64B5F6'>◈</span> Intent Analyst<br>
    &nbsp;&nbsp;↓<br>
    <span style='color:#81C784'>◉</span> Prompt Engineer<br>
    &nbsp;&nbsp;↓<br>
    <span style='color:#CE93D8'>◆</span> Knowledge Agent
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Main Header
# ─────────────────────────────────────────────
st.markdown('<div class="main-title">Multi-Agent Query Intelligence</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">INTENT → OPTIMIZE → RESPOND</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def copy_button(text: str, key: str):
    """Render a copy-to-clipboard button using streamlit components."""
    escaped = text.replace("`", "\\`").replace("$", "\\$")
    st.components.v1.html(f"""
    <button onclick="navigator.clipboard.writeText(`{escaped}`).then(()=>{{
        this.innerText='✓ Copied!';
        setTimeout(()=>this.innerText='⎘ Copy',1500);
    }})"
    style="background:#0d2137;border:1px solid #1e3f5e;color:#90caf9;
           padding:4px 12px;border-radius:6px;cursor:pointer;
           font-family:monospace;font-size:11px;letter-spacing:1px;
           transition:all 0.2s;">
        ⎘ Copy
    </button>
    """, height=36)


def render_intent(intent: dict):
    category = intent.get("category", "other")
    clarity = intent.get("clarity", "medium")
    cat_color = CATEGORY_COLORS.get(category, "#90A4AE")
    cl_color = CLARITY_COLORS.get(clarity, "#aaa")

    st.markdown(f"""
    <div class="intent-box">
        <div class="section-label" style="color:#64B5F6">◈ INTENT ANALYSIS</div>
        <div style="color:#e0e0e0;margin-bottom:8px">{intent.get('intent','')}</div>
        <span class="tag" style="color:{cat_color}">{category}</span>
        <span class="tag" style="color:{cl_color}">clarity: {clarity}</span>
    </div>
    """, unsafe_allow_html=True)

    missing = intent.get("missing", [])
    if missing:
        with st.expander("Missing context identified", expanded=False):
            for m in missing:
                st.markdown(f"• {m}")

    keywords = intent.get("keywords", [])
    if keywords:
        st.caption("Keywords: " + " · ".join(f"`{k}`" for k in keywords))


def render_improved(improved: dict):
    prompt_text = improved.get("improved_prompt", "")
    st.markdown(f"""
    <div class="improved-box">
        <div class="section-label" style="color:#81C784">◉ OPTIMIZED PROMPT</div>
        <div style="color:#c8e6c9;font-style:italic;margin-bottom:8px">"{prompt_text}"</div>
    </div>
    """, unsafe_allow_html=True)

    copy_button(prompt_text, key=f"copy_prompt_{hash(prompt_text)}")

    changes = improved.get("changes", [])
    if changes:
        with st.expander("What was improved", expanded=False):
            for c in changes:
                st.markdown(f"↗ {c}")
    gain = improved.get("expected_quality_gain", "")
    if gain:
        st.caption(f"Expected gain: {gain}")


def render_response(response: str, msg_idx: int):
    st.markdown(f"""
    <div class="response-box">
        <div class="section-label" style="color:#CE93D8">◆ KNOWLEDGE AGENT RESPONSE</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(response)
    copy_button(response, key=f"copy_resp_{msg_idx}")


def render_message(msg: dict, idx: int):
    if msg["role"] != "user":
        return

    ts = msg.get("ts", "")
    model_used = msg.get("model", "")

    st.markdown(f"""
    <div class="user-msg">
        <span style="color:#4a8abf">▷ You</span>
        <span class="timestamp">{ts} · <code style="font-size:0.6rem">{model_used}</code></span>
        <br><br>{msg['content']}
        {'&nbsp;<span style="background:#1b5e20;color:#81C784;font-size:9px;padding:1px 6px;border-radius:3px;vertical-align:middle;font-family:monospace;letter-spacing:1px">OPTIMIZED</span>' if msg.get('is_improved') else ''}
    </div>
    """, unsafe_allow_html=True)

    if msg.get("intent"):
        render_intent(msg["intent"])

    if msg.get("improved"):
        render_improved(msg["improved"])

    if msg.get("response"):
        render_response(msg["response"], idx)

    st.markdown("<br>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Chat Display
# ─────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("""
    <div style="text-align:center;padding:60px 20px;color:#2a3a4a">
        <div style="font-size:3rem;letter-spacing:12px;color:#1e2d3d">◈◉◆</div>
        <div style="font-family:'Crimson Pro',serif;font-size:1.5rem;color:#3a5a6a;margin-top:12px;font-weight:300">
            Ask anything. Our agents will perfect it.
        </div>
        <div style="font-size:0.8rem;margin-top:8px;color:#1e2d3d;max-width:500px;margin-left:auto;margin-right:auto;line-height:1.7">
            The pipeline analyzes your intent, crafts an optimized version, and delivers a superior answer.
        </div>
    </div>
    """, unsafe_allow_html=True)

    example_queries = [
        "tell me about machine learning",
        "how do I make my Python code faster",
        "explain how transformer models work",
        "best practices for building REST APIs",
    ]
    st.markdown("**Try an example:**")
    cols = st.columns(2)
    for i, q in enumerate(example_queries):
        if cols[i % 2].button(f'"{q}"', key=f"example_{i}", use_container_width=True):
            st.session_state["prefill_query"] = q
            st.rerun()

else:
    for i, msg in enumerate(st.session_state.messages):
        render_message(msg, i)


# ─────────────────────────────────────────────
# Input & Processing
# ─────────────────────────────────────────────
st.markdown("---")

prefill = st.session_state.pop("prefill_query", "")

with st.form("chat_form", clear_on_submit=True):
    col_input, col_send = st.columns([6, 1])
    with col_input:
        user_input = st.text_area(
            "Your query",
            value=prefill,
            placeholder="Type your query here... (Shift+Enter for newline)",
            height=80,
            label_visibility="collapsed",
        )
    with col_send:
        submitted = st.form_submit_button(
            "▷ Send",
            use_container_width=True,
            disabled=st.session_state.processing or not api_key,
        )

st.caption(
    "3-AGENT PIPELINE: INTENT ANALYSIS → PROMPT OPTIMIZATION → INTELLIGENT RESPONSE  |  "
    f"Model: `{model_id}`"
)


# ─────────────────────────────────────────────
# Run Pipeline
# ─────────────────────────────────────────────
if submitted and user_input.strip() and api_key:
    st.session_state.processing = True

    # Build history for context (last 10 turns)
    history_context = []
    for msg in st.session_state.messages[-10:]:
        history_context.append({"role": "user", "content": msg["content"]})
        if msg.get("response"):
            history_context.append({"role": "assistant", "content": msg["response"]})

    # Show live agent status
    status_placeholder = st.empty()
    with status_placeholder.container():
        st.markdown("**Pipeline running...**")
        p1, p2, p3 = st.columns(3)
        p1.info("◈ Intent Analyst\n\n_analyzing..._")
        p2.empty()
        p3.empty()

    time.sleep(0.3)

    try:
        # ── Run the LangGraph pipeline ──
        result = run_pipeline(
            query=user_input.strip(),
            model=model_id,
            chat_history=history_context,
            use_improved=st.session_state.use_improved,
        )

        status_placeholder.empty()

        if result.get("error"):
            st.error(f"Pipeline error: {result['error']}")
        else:
            # Save to session
            st.session_state.messages.append({
                "role": "user",
                "content": user_input.strip(),
                "intent": result.get("intent_analysis"),
                "improved": result.get("improved_prompt"),
                "response": result.get("final_response"),
                "model": model_id,
                "ts": datetime.now().strftime("%H:%M"),
                "is_improved": st.session_state.use_improved,
            })

    except Exception as e:
        status_placeholder.empty()
        st.error(f"Unexpected error: {str(e)}")

    st.session_state.processing = False
    st.rerun()
