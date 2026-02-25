"""
styles.py – Minimal CSS polish on top of config.toml dark theme.
We rely on Streamlit native components (st.chat_message, st.chat_input)
instead of custom HTML bubbles.
"""

import streamlit as st


POLISH_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Font */
    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

    /* Sidebar width & clean look */
    [data-testid="stSidebar"] {
        min-width: 260px !important;
        max-width: 300px !important;
        border-right: 1px solid rgba(255,255,255,0.07);
    }

    /* Sidebar session buttons — look like ChatGPT conversation list */
    [data-testid="stSidebar"] .stButton button {
        background: transparent;
        border: none;
        border-radius: 8px;
        text-align: left;
        color: #ECECEC;
        font-size: 14px;
        padding: 8px 12px;
        transition: background 0.15s ease;
        user-select: none !important;
        -webkit-user-select: none !important;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        background: rgba(255,255,255,0.07) !important;
        border: none;
        box-shadow: none;
    }

    /* Active session button — subtle tint, no heavy border */
    [data-testid="stSidebar"] .stButton button[data-testid="baseButton-primary"],
    [data-testid="stSidebar"] .stButton button[data-testid="stBaseButton-primary"],
    [data-testid="stSidebar"] .stButton:has(button[kind="primary"]) button {
        background: rgba(124, 106, 247, 0.18) !important;
        color: #d4cfff !important;
        border: none !important;
        border-left: 2px solid rgba(124, 106, 247, 0.7) !important;
        box-shadow: none !important;
    }
    [data-testid="stSidebar"] .stButton button[data-testid="baseButton-primary"]:hover,
    [data-testid="stSidebar"] .stButton button[data-testid="stBaseButton-primary"]:hover,
    [data-testid="stSidebar"] .stButton:has(button[kind="primary"]) button:hover {
        background: rgba(124, 106, 247, 0.26) !important;
    }

    /* Trash delete button — subtle icon, no border */
    [data-testid="stSidebar"] [data-testid^="del_"] button,
    [data-testid="stSidebar"] .stButton:has(button[title="Apagar sessão"]) button {
        background: transparent !important;
        border: none !important;
        color: rgba(255,255,255,0.3) !important;
        padding: 4px !important;
        font-size: 13px !important;
        min-height: 0 !important;
        box-shadow: none !important;
    }
    [data-testid="stSidebar"] .stButton:has(button[title="Apagar sessão"]) button:hover {
        color: #ff6b6b !important;
        background: rgba(255,100,100,0.1) !important;
    }

    /* Popover button (⋯) — tiny */
    [data-testid="stSidebar"] [data-testid="stPopover"] button {
        background: transparent !important;
        border: none !important;
        color: rgba(255,255,255,0.4) !important;
        font-size: 18px;
        padding: 4px 8px !important;
        min-height: 0 !important;
    }
    [data-testid="stSidebar"] [data-testid="stPopover"] button:hover {
        color: white !important;
        background: rgba(255,255,255,0.08) !important;
    }

    /* Main chat area — centered like ChatGPT */
    .main .block-container {
        max-width: 860px !important;
        padding: 2rem 1rem 6rem 1rem !important;
        margin: 0 auto;
    }

    /* Chat messages */
    [data-testid="stChatMessage"] {
        border-radius: 12px;
        margin-bottom: 4px;
    }

    /* User bubble */
    [data-testid="stChatMessage"][data-testid*="user"],
    .stChatMessage.user {
        background: rgba(124,106,247,0.12) !important;
    }

    /* Assistant bubble */
    [data-testid="stChatMessage"][data-testid*="assistant"],
    .stChatMessage.assistant {
        background: rgba(255,255,255,0.03) !important;
    }

    /* Chat input — sticky bottom */
    [data-testid="stChatInput"] {
        border-radius: 12px !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        background: #1A1C24 !important;
    }
    [data-testid="stChatInput"]:focus-within {
        border-color: #7C6AF7 !important;
        box-shadow: 0 0 0 2px rgba(124,106,247,0.25) !important;
    }

    /* Expander (reasoning panel) */
    [data-testid="stExpander"] {
        border-radius: 8px !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        background: rgba(255,255,255,0.02) !important;
    }

    /* Title gradient */
    h1 {
        background: linear-gradient(90deg, #7C6AF7, #B39DDB);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }

    /* Hide only Streamlit branding elements, NOT the sidebar toggle */
    #MainMenu, footer { visibility: hidden; }
    header[data-testid="stHeader"] { background: transparent !important; }

    /* Disable sidebar collapse button & deploy button */
    [data-testid="stSidebarCollapseButton"] { display: none !important; }
    [data-testid="stAppDeployButton"]        { display: none !important; }

    /* Sidebar expand button (shown when sidebar is collapsed) — always visible */
    [data-testid="stSidebarCollapsedControl"] {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        visibility: visible !important;
        opacity: 1 !important;
        z-index: 999999 !important;
        position: fixed !important;
        left: 0 !important;
        top: 48% !important;
        width: 28px !important;
        height: 48px !important;
        background: #1A1C24 !important;
        border: 1px solid rgba(255,255,255,0.18) !important;
        border-left: none !important;
        border-radius: 0 10px 10px 0 !important;
        box-shadow: 3px 0 10px rgba(0,0,0,0.5) !important;
        cursor: pointer !important;
        transition: background 0.2s ease, width 0.2s ease !important;
    }
    [data-testid="stSidebarCollapsedControl"]:hover {
        background: #7C6AF7 !important;
        width: 34px !important;
    }
    [data-testid="stSidebarCollapsedControl"] svg {
        color: #ECECEC !important;
        fill: #ECECEC !important;
    }
</style>
"""


def inject_css() -> None:
    st.markdown(POLISH_CSS, unsafe_allow_html=True)
