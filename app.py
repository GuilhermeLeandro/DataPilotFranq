"""
app.py – DataPilot entry point.
Uses native Streamlit chat components (st.chat_message, st.chat_input).
"""

import streamlit as st

from src.config import APP_TITLE, APP_ICON
from src.ui.styles import inject_css
from src.ui.sidebar import render_sidebar
from src.ui.chat import render_chat_history, get_user_input, render_new_message
from src.agent.graph import run_agent
from src import history

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="wide")
inject_css()

# ── Init DB ────────────────────────────────────────────────────────────────────
history.init_db()

# ── Session State Init (lazy — no DB row until first message) ─────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = None
    st.session_state.messages = []

# ── Layout ─────────────────────────────────────────────────────────────────────
render_sidebar()

# Header (shown only when chat is empty)
if not st.session_state.messages:
    st.markdown("# 🚀 DataPilot")
    st.markdown("**Assistente Virtual de Dados** — Faça perguntas em linguagem natural sobre os dados da empresa.")
    st.divider()

# ── Chat History ───────────────────────────────────────────────────────────────
render_chat_history()

# ── Input & Agent Call (st.chat_input is sticky at the bottom automatically) ──
question = get_user_input()

if question:
    # Lazily create the DB session on first message
    if st.session_state.session_id is None:
        st.session_state.session_id = history.create_session()

    session_id: str = st.session_state.session_id

    # Immediately show user message (streaming feel)
    user_msg = {"role": "user", "content": question}
    st.session_state.messages.append(user_msg)
    render_new_message("user", question)

    is_first_message = len(st.session_state.messages) == 1  # just appended user msg

    # Persist user message
    history.save_message(session_id, role="user", content=question)

    # On first message: generate an LLM title in a background thread (non-blocking)
    if is_first_message:
        import threading
        from src.agent.title_agent import generate_session_title
        def _set_title():
            title = generate_session_title(question)
            history.rename_session(session_id, title)
        threading.Thread(target=_set_title, daemon=True).start()

    # Build context (last 20 messages = 10 exchanges)
    context = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages[-20:]
        if m.get("content")
    ]

    # ── Streaming response ─────────────────────────────────────────────────────
    from src.agent.graph import stream_agent_response
    from src.ui.charts import render_result

    with st.chat_message("assistant", avatar="🤖"):
        text_placeholder = st.empty()
        status_placeholder = st.empty()

        status_placeholder.markdown("*🔍 Consultando banco de dados...*")

        full_text = ""
        sql_steps: list[str] = []
        last_result = None
        got_first_token = False
        error_msg = None

        for event in stream_agent_response(question, chat_history=context[:-1]):
            if event["type"] == "token":
                if not got_first_token:
                    status_placeholder.empty()
                    got_first_token = True
                full_text += event["content"]
                text_placeholder.markdown(full_text + "▌")  # blinking cursor effect

            elif event["type"] == "done":
                text_placeholder.markdown(full_text or "*Sem resposta.*")
                sql_steps = event.get("sql_steps", [])
                last_result = event.get("last_result")

            elif event["type"] == "error":
                status_placeholder.empty()
                error_msg = event["content"]
                full_text = f"❌ Erro: {error_msg}"
                text_placeholder.markdown(full_text)

        if last_result:
            render_result(last_result, question)

        if sql_steps:
            with st.expander("🧠 Ver raciocínio e queries executadas"):
                for i, sql in enumerate(sql_steps, 1):
                    st.markdown(f"**Query {i}:**")
                    st.code(sql, language="sql")

    # Persist assistant message & save to state
    bot_msg = {
        "role": "assistant",
        "content": full_text,
        "sql_steps": sql_steps,
        "question": question,
        "viz_data": last_result,
    }
    history.save_message(
        session_id,
        role="assistant",
        content=full_text,
        question=question,
        sql_steps=sql_steps,
        viz_data=last_result,
    )
    st.session_state.messages.append(bot_msg)

    # Force sidebar to update immediately after first message
    # (sidebar renders before session creation, so needs rerun to show new session)
    if is_first_message:
        st.rerun()
