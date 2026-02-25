import sqlite3
import os
from pathlib import Path
from typing import Any

from src.config import DB_PATH


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_schema() -> str:
    """
    Dynamically reads the database schema and returns a formatted string
    describing all tables and their columns.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]

    schema_parts = []
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        col_defs = ", ".join(
            f"{col[1]} ({col[2]})" for col in columns
        )
        # Grab a few sample values to help the LLM understand the data
        cursor.execute(f"SELECT * FROM {table} LIMIT 3")
        samples = cursor.fetchall()
        sample_str = ""
        if samples:
            sample_str = "\n  Sample rows:\n"
            for row in samples:
                sample_str += f"    {dict(row)}\n"
        schema_parts.append(f"Table: {table}\n  Columns: {col_defs}{sample_str}")

    conn.close()
    return "\n\n".join(schema_parts)


def run_query(sql: str) -> tuple[list[str], list[tuple[Any, ...]]]:
    """
    Executes a SQL query and returns (column_names, rows).
    Raises RuntimeError with a descriptive message on failure.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description] if cursor.description else []
        return columns, [tuple(row) for row in rows]
    except sqlite3.Error as e:
        raise RuntimeError(f"SQL execution error: {e}\nQuery attempted:\n{sql}") from e
    finally:
        conn.close()
