"""The tools our agent is allowed to use, and the database behind them.

A "tool" is just a normal Python function plus a description the model can
read. The model never runs anything itself: it asks, our code decides
whether to run it, and sends the result back as text.

Used by 02_agent_with_tools.py and exercise.py.
"""

import json
import sqlite3
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MAX_ROWS = 20


def build_database():
    """Load the CSV files into a temporary in-memory SQLite database.

    Day 2 built the database by hand. pandas can do it in one line per table.
    """
    conn = sqlite3.connect(":memory:")
    for table in ["tickets", "customers", "agents"]:
        pd.read_csv(DATA_DIR / f"{table}.csv").to_sql(table, conn, index=False)

    policy = json.loads((DATA_DIR / "sla_policy.json").read_text(encoding="utf-8"))
    targets = pd.DataFrame(policy["targets"]).T.rename_axis("priority").reset_index()
    targets.to_sql("sla_targets", conn, index=False)

    # Guardrail 1: from here on the database itself rejects any change.
    conn.execute("PRAGMA query_only = ON")
    return conn


DB = build_database()


def get_schema():
    """List the tables and their columns."""
    lines = []
    tables = DB.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")
    for (table,) in tables.fetchall():
        columns = DB.execute(f"SELECT name FROM pragma_table_info('{table}')").fetchall()
        lines.append(f"{table}: " + ", ".join(name for (name,) in columns))
    return "\n".join(lines)


def run_sql(query):
    """Run one read-only SQL query and return the rows as text.

    Problems come back as text starting with REFUSED or ERROR instead of
    crashing, so the model can read what went wrong and try again.
    """
    cleaned = query.strip().rstrip(";")

    # Guardrail 2: only questions, never changes. One statement at a time.
    if not cleaned.lower().startswith(("select", "with")):
        return "REFUSED: only SELECT queries are allowed. This tool cannot change data."
    if ";" in cleaned:
        return "REFUSED: one statement at a time."

    try:
        cursor = DB.execute(cleaned)
    except sqlite3.Error as error:
        return f"ERROR: {error}"

    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchmany(MAX_ROWS + 1)

    # Guardrail 3: never flood the model (or the bill) with thousands of rows.
    truncated = len(rows) > MAX_ROWS
    lines = [" | ".join(columns)]
    lines += [" | ".join("" if value is None else str(value) for value in row)
              for row in rows[:MAX_ROWS]]
    if truncated:
        lines.append(f"... only the first {MAX_ROWS} rows are shown")
    return "\n".join(lines)


# name -> function. The agent loop looks tools up here.
TOOL_FUNCTIONS = {
    "get_schema": get_schema,
    "run_sql": run_sql,
}

# What the model gets to read. Good descriptions matter as much as good prompts:
# this text is the only thing the model knows about each tool.
TOOL_DEFINITIONS = [
    {
        "name": "get_schema",
        "description": "List the tables and columns of the support database. "
                       "Call this first, before writing any SQL.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "run_sql",
        "description": "Run one read-only SQLite SELECT query against the support database "
                       f"and get the rows back as text (at most {MAX_ROWS} rows). "
                       "Timestamps are text like '2026-10-14 09:24:26'. "
                       "Unresolved tickets have status 'open' or 'pending'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "A single SQLite SELECT statement."},
            },
            "required": ["query"],
        },
    },
]
