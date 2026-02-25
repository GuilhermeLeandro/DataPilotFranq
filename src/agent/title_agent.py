"""
title_agent.py – Lightweight LLM agent to generate a short session title.

Called once per session, after the very first user message.
Uses a cheap, fast call (gpt-4o-mini) with low token budget.
"""

from __future__ import annotations

from langchain_openai import ChatOpenAI
from src.config import MODEL


def generate_session_title(question: str) -> str:
    """
    Generates a concise session title (max 6 words, no punctuation at the end)
    based on the user's first question.

    Falls back to a simple truncation if the LLM call fails.
    """
    try:
        llm = ChatOpenAI(model=MODEL, temperature=0, max_tokens=20)
        prompt = (
            "Crie um título curto (máximo 6 palavras, sem ponto final) "
            "que resume essa pergunta em português. Responda APENAS o título, "
            "sem aspas, sem explicações.\n\n"
            f"Pergunta: {question}"
        )
        response = llm.invoke(prompt)
        title = response.content.strip().strip('"').strip("'").strip(".")
        # Safety: cap at 60 chars
        return title[:60] if title else _fallback(question)
    except Exception:
        return _fallback(question)


def _fallback(question: str) -> str:
    return question[:57] + "…" if len(question) > 57 else question
