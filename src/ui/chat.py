"""
chat.py – Chat rendering using native Streamlit components.
Uses st.chat_message() and st.chat_input() for a proper ChatGPT-style UX.
"""

from __future__ import annotations

import streamlit as st

from src.ui.charts import render_result


def render_chat_history() -> None:
    """Renders all messages from st.session_state.messages using native st.chat_message."""
    for msg in st.session_state.get("messages", []):
        _render_message(msg)


def get_user_input() -> str | None:
    """
    Renders the sticky chat input at the bottom of the page.
    Returns the submitted text or None.
    Uses st.chat_input() which is automatically sticky and clears on submit.
    """
    return st.chat_input("Faça uma pergunta sobre os dados...")


def render_new_message(role: str, content: str) -> None:
    """Renders a single new message immediately (used after append, before rerun)."""
    _render_message({"role": role, "content": content})


# ── Private ────────────────────────────────────────────────────────────────────

def _render_message(msg: dict) -> None:
    role = msg["role"]
    avatar = "🤖" if role == "assistant" else "👤"

    with st.chat_message(role, avatar=avatar):
        st.markdown(msg["content"])

        # Visualization (only for assistant messages with data)
        if role == "assistant" and msg.get("viz_data"):
            render_result(msg["viz_data"], msg.get("question", ""))

        # Reasoning expander
        if role == "assistant" and msg.get("sql_steps"):
            with st.expander("🧠 Ver raciocínio e queries executadas"):
                for i, sql in enumerate(msg["sql_steps"], 1):
                    st.markdown(f"**Query {i}:**")
                    st.code(sql, language="sql")
