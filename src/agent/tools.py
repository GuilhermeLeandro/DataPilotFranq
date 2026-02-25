"""
tools.py – LangChain tools for the SQL agent.
"""

import json
from langchain_core.tools import tool
from src.database import get_schema, run_query


@tool
def get_db_schema() -> str:
    """
    Returns the complete database schema including all table names,
    column names, data types, and a few sample rows.
    Always call this first before writing any SQL query.
    """
    return get_schema()


@tool
def execute_sql(query: str) -> str:
    """
    Executes a SQLite SQL query against the business database.
    Returns the results as a JSON string with keys 'columns' and 'rows'.
    If the query fails, returns an error message starting with 'ERROR:'.
    Use this to retrieve data, counts, aggregations, etc.

    Args:
        query: A valid SQLite SQL SELECT statement.
    """
    try:
        columns, rows = run_query(query)
        if not rows:
            return json.dumps({"columns": columns, "rows": [], "message": "Query returned no results."})
        # Limit to 500 rows to avoid context overflow
        truncated = len(rows) > 500
        result = {
            "columns": columns,
            "rows": [list(r) for r in rows[:500]],
            "row_count": len(rows),
        }
        if truncated:
            result["message"] = f"Results truncated to 500 rows out of {len(rows)} total."
        return json.dumps(result, default=str, ensure_ascii=False)
    except RuntimeError as e:
        return f"ERROR: {e}"
