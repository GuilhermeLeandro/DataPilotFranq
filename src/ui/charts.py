"""
charts.py – Plotly chart rendering for DataPilot.
Bridges the chart_advisor recommendation with actual Plotly figures.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.viz.chart_advisor import recommend_viz

_PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(255,255,255,0.03)",
    font=dict(color="#e8eaf6"),
)


def render_result(viz_data: dict, question: str) -> None:
    """
    Given raw result data {columns, rows} and the original question,
    renders the most appropriate visualization (bar, line, pie, or table).
    """
    columns: list[str] = viz_data.get("columns", [])
    rows: list[list] = viz_data.get("rows", [])

    if not columns or not rows:
        return

    df = pd.DataFrame(rows, columns=columns)
    rec = recommend_viz(question, columns, rows)

    dispatch = {
        "bar":  _render_bar,
        "line": _render_line,
        "pie":  _render_pie,
    }

    renderer = dispatch.get(rec["type"])
    if renderer and rec["x"] in df.columns and rec["y"] in df.columns:
        renderer(df, rec)
    else:
        _render_table(df)


# ── Private renderers ──────────────────────────────────────────────────────────

def _render_bar(df: pd.DataFrame, rec: dict) -> None:
    fig = px.bar(
        df, x=rec["x"], y=rec["y"], title=rec.get("title", ""),
        color=rec["y"], color_continuous_scale="Viridis",
        template="plotly_dark",
    )
    fig.update_layout(**_PLOTLY_LAYOUT, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


def _render_line(df: pd.DataFrame, rec: dict) -> None:
    # Use a second categorical column for multi-line if available
    cat_cols = [c for c in df.columns if c != rec["y"] and pd.api.types.is_string_dtype(df[c])]
    color_col = cat_cols[1] if len(cat_cols) > 1 else None
    fig = px.line(
        df, x=rec["x"], y=rec["y"], color=color_col,
        title=rec.get("title", ""), template="plotly_dark", markers=True,
    )
    fig.update_layout(**_PLOTLY_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)


def _render_pie(df: pd.DataFrame, rec: dict) -> None:
    fig = px.pie(
        df, names=rec["x"], values=rec["y"], title=rec.get("title", ""),
        template="plotly_dark",
        color_discrete_sequence=px.colors.sequential.Viridis,
    )
    fig.update_layout(**_PLOTLY_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)


def _render_table(df: pd.DataFrame) -> None:
    st.dataframe(df, use_container_width=True, hide_index=True)
