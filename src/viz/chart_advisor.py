"""
chart_advisor.py – Heuristic-based visualization recommender.
"""

from __future__ import annotations
import re


# Keywords that suggest time-based line charts
TIME_KEYWORDS = [
    "tendência", "tendencia", "evolução", "evolucao", "ao longo",
    "por mês", "por mes", "mensal", "mensal", "histórico", "historico",
    "último ano", "ultimo ano", "últimos meses", "ultimos meses",
    "por trimestre", "trimestral", "por ano", "anual", "time series",
]

# Keywords that suggest ranked bar charts
RANK_KEYWORDS = [
    "top", "maior", "menor", "ranking", "mais", "menos",
    "primeiro", "melhor", "pior", "mais frequente", "mais vendido",
]

# Keywords that suggest a pie / distribution chart
PIE_KEYWORDS = [
    "proporção", "proporcao", "distribuição", "distribuicao",
    "percentual", "porcentagem", "fatia",
]


def recommend_viz(
    question: str,
    columns: list[str],
    rows: list[list],
) -> dict:
    """
    Returns a dict describing how to visualize the data:
    {
        "type": "bar" | "line" | "pie" | "table",
        "x": column_name,
        "y": column_name,
        "title": str,
    }
    """
    q = question.lower()

    # Identify categorical and numeric columns
    categorical_cols = []
    numeric_cols = []

    if rows:
        for i, col in enumerate(columns):
            sample = rows[0][i] if rows else None
            if isinstance(sample, (int, float)):
                numeric_cols.append(col)
            else:
                categorical_cols.append(col)
    else:
        return {"type": "table", "x": None, "y": None, "title": "Resultado"}

    # Single value → just show as text (still table)
    if len(columns) == 1 and len(rows) == 1:
        return {"type": "table", "x": None, "y": None, "title": "Resultado"}

    # Need at least one categorical + one numeric for a chart
    has_chart_shape = len(categorical_cols) >= 1 and len(numeric_cols) >= 1

    if has_chart_shape:
        x_col = categorical_cols[0]
        y_col = numeric_cols[0]

        if any(kw in q for kw in TIME_KEYWORDS):
            return {"type": "line", "x": x_col, "y": y_col, "title": "Tendência ao longo do tempo"}

        if any(kw in q for kw in PIE_KEYWORDS) and len(rows) <= 8:
            return {"type": "pie", "x": x_col, "y": y_col, "title": "Distribuição"}

        if any(kw in q for kw in RANK_KEYWORDS) or len(rows) <= 20:
            return {"type": "bar", "x": x_col, "y": y_col, "title": "Comparação"}

    # Default fallback
    return {"type": "table", "x": None, "y": None, "title": "Resultado"}
