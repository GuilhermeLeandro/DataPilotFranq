"""
sidebar.py – Sidebar component for DataPilot.
Layout:
  🤖 DataPilot
  ─────────────
  [✏️ Nova conversa]
  ─────────────
  Chats criados
    ▶ Session 1  ⋯
       Session 2  ⋯
  ─────────────
  DataPilot v1.0
"""

from datetime import datetime

import streamlit as st

from src.config import APP_VERSION
from src import history


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("## 🤖 DataPilot")
        st.divider()

        # ── Nova conversa (no icon, clean button) ─────────────────────────────
        if st.button("✏️  Nova conversa", use_container_width=True, type="primary"):
            # Only resets state — DB session is created on first message
            st.session_state.session_id = None
            st.session_state.messages = []
            st.rerun()

        st.divider()

        # ── Session list ───────────────────────────────────────────────────────
        st.caption("CHATS CRIADOS")
        _render_sessions_section()

        st.divider()
        st.markdown(
            f"""<div style='font-size:11px; color: rgba(255,255,255,0.3);'>
            DataPilot v{APP_VERSION} · LangGraph + OpenAI</div>""",
            unsafe_allow_html=True,
        )


# ── Private ────────────────────────────────────────────────────────────────────

def _render_sessions_section() -> None:
    sessions = history.list_sessions(limit=20)
    current_id = st.session_state.get("session_id")

    if not sessions:
        st.caption("Nenhuma conversa ainda.")
        return

    for s in sessions:
        is_current = s["id"] == current_id
        label = s["title"]
        short = label[:30] + ("…" if len(label) > 30 else "")

        col_btn, col_del = st.columns([5, 1])

        with col_btn:
            btn_type = "primary" if is_current else "secondary"
            if st.button(
                short,
                key=f"sess_{s['id']}",
                use_container_width=True,
                type=btn_type,
                help=_fmt_date(s["updated_at"]),
            ):
                st.session_state.session_id = s["id"]
                st.session_state.messages = history.load_messages(s["id"])
                st.rerun()

        with col_del:
            if st.button("🗑️", key=f"del_{s['id']}", help="Apagar sessão"):
                history.delete_session(s["id"])
                if s["id"] == current_id:
                    st.session_state.session_id = None
                    st.session_state.messages = []
                st.rerun()


def _fmt_date(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%d/%m %H:%M")
    except Exception:
        return iso_str
