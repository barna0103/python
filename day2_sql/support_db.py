"""Shared helper for Day 2: build the SQLite database and print query results.

You do not run this file directly. The numbered scripts import it:

    from support_db import connect, show

SQLite is a full SQL database that lives in one file and ships with Python,
so there is nothing to install and no server to start.
"""

import csv
import json
import sqlite3
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE.parent / "data"
DB_FILE = HERE / "output" / "support.db"

# The table designs. Each line is: column name, type, optional rule.
SCHEMA = """
CREATE TABLE customers (
    customer_id  TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    plan         TEXT NOT NULL,      -- Free, Pro or Enterprise
    region       TEXT NOT NULL,
    signup_date  TEXT NOT NULL,
    mrr_usd      INTEGER NOT NULL    -- monthly recurring revenue
);

CREATE TABLE agents (
    agent_id  TEXT PRIMARY KEY,
    name      TEXT NOT NULL,
    team      TEXT NOT NULL          -- Tier 1, Tier 2 or Escalations
);

CREATE TABLE sla_targets (
    priority                TEXT PRIMARY KEY,
    first_response_minutes  INTEGER NOT NULL,
    resolution_hours        INTEGER NOT NULL
);

CREATE TABLE tickets (
    ticket_id          TEXT PRIMARY KEY,
    customer_id        TEXT NOT NULL REFERENCES customers (customer_id),
    agent_id           TEXT NOT NULL REFERENCES agents (agent_id),
    created_at         TEXT NOT NULL,
    first_response_at  TEXT,         -- NULL = nobody has replied yet
    resolved_at        TEXT,         -- NULL = not resolved yet
    priority           TEXT NOT NULL REFERENCES sla_targets (priority),
    category           TEXT NOT NULL,
    status             TEXT NOT NULL,
    escalated          INTEGER NOT NULL,   -- 1 = yes, 0 = no
    csat               INTEGER,            -- 1 to 5, NULL = no survey answer
    subject            TEXT NOT NULL
);
"""


def read_csv(name):
    """Read data/<name>.csv into a list of dicts, turning empty text into None.

    None in Python becomes NULL in SQL, which is how a database says "no value".
    """
    with open(DATA_DIR / f"{name}.csv", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return [{key: (value if value != "" else None) for key, value in row.items()} for row in rows]


def insert_rows(conn, table, rows):
    """Insert a list of dicts into a table.

    The :name placeholders are filled in by SQLite itself. Never paste values
    into SQL text by hand: placeholders keep odd characters (and attackers) out.
    """
    columns = list(rows[0].keys())
    placeholders = ", ".join(f":{column}" for column in columns)
    sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
    conn.executemany(sql, rows)


def build_database():
    """Create output/support.db from the CSV and JSON files in data/."""
    DB_FILE.parent.mkdir(exist_ok=True)
    DB_FILE.unlink(missing_ok=True)          # start fresh every time

    conn = sqlite3.connect(DB_FILE)
    conn.executescript(SCHEMA)

    for table in ["customers", "agents", "tickets"]:
        insert_rows(conn, table, read_csv(table))

    policy = json.loads((DATA_DIR / "sla_policy.json").read_text(encoding="utf-8"))
    targets = [{"priority": priority, **numbers} for priority, numbers in policy["targets"].items()]
    insert_rows(conn, "sla_targets", targets)

    conn.commit()                            # save the changes to the file
    conn.close()
    return DB_FILE


def connect():
    """Open the database (building it first if it does not exist yet)."""
    if not DB_FILE.exists():
        build_database()
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row           # lets us read columns by name
    return conn


def format_table(columns, rows):
    """Turn query results into a plain text table."""
    cells = [["" if value is None else str(value) for value in row] for row in rows]
    widths = [max(len(str(column)), *(len(row[i]) for row in cells)) if cells else len(str(column))
              for i, column in enumerate(columns)]
    lines = ["  ".join(str(column).ljust(width) for column, width in zip(columns, widths)),
             "  ".join("-" * width for width in widths)]
    lines += ["  ".join(cell.ljust(width) for cell, width in zip(row, widths)) for row in cells]
    return "\n".join(lines)


def show(conn, title, sql, params=()):
    """Print a heading, the SQL, and the rows it returns."""
    cursor = conn.execute(sql, params)
    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()
    print(f"\n=== {title} ===")
    print("\n".join("    " + line for line in sql.strip().splitlines()))
    if params:
        print(f"    -- values: {params}")
    print()
    print(format_table(columns, rows))
    return rows
