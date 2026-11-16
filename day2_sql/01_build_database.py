"""Day 2, example 1: turn CSV files into a real SQL database.

Run it:   python day2_sql/01_build_database.py

Scenario: the helpdesk export is too big and too connected for a spreadsheet.
Load it into a database once, then ask as many questions as you like.

The loading code lives in support_db.py (worth a skim: it is 4 small
functions). This script runs it and shows you what was built.
"""

from support_db import build_database, connect, show

db_file = build_database()
print(f"Built {db_file.name} ({db_file.stat().st_size / 1024:.0f} KB) in {db_file.parent}")

conn = connect()

# Every SQLite database can describe itself. Handy when you inherit one.
show(conn, "Tables in this database",
     "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")

print("\nRows per table:")
for table in ["customers", "agents", "sla_targets", "tickets"]:
    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"  {table:<12} {count:>4}")

show(conn, "Columns of the tickets table",
     "SELECT name, type FROM pragma_table_info('tickets')")

show(conn, "First three tickets",
     "SELECT ticket_id, customer_id, priority, category, status FROM tickets LIMIT 3")

conn.close()
