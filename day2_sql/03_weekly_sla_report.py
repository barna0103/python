"""Day 2, example 3: a weekly SLA report from one saved SQL file.

Run it:   python day2_sql/03_weekly_sla_report.py

Scenario: every Monday the support lead wants volume, SLA compliance and
satisfaction per week. The question lives in queries/weekly_sla_report.sql,
so it is the same every week and anyone can review it.

This script: runs the saved query -> prints it -> writes a Markdown report.
"""

from pathlib import Path

from support_db import connect, format_table

HERE = Path(__file__).resolve().parent
REPORT_TIME = "2026-11-02 09:00:00"     # fixed "now", same as data/sla_policy.json
SLA_GOAL_PCT = 85.0                     # the team's promise: 85% answered in time

sql = (HERE / "queries" / "weekly_sla_report.sql").read_text(encoding="utf-8")

conn = connect()
cursor = conn.execute(sql, {"report_time": REPORT_TIME})   # fills in :report_time
columns = [column[0] for column in cursor.description]
rows = cursor.fetchall()
conn.close()

print("Weekly support report\n")
print(format_table(columns, rows))

# Each row behaves like a dict: row["tickets"], row["sla_met_pct"] ...
missed = [row for row in rows if row["sla_met_pct"] < SLA_GOAL_PCT]
busiest = max(rows, key=lambda row: row["tickets"])

print(f"\nWeeks below the {SLA_GOAL_PCT:.0f}% SLA goal: {len(missed)} of {len(rows)}")
for row in missed:
    print(f"  week of {row['week_start']}: {row['sla_met_pct']}% "
          f"({row['breached']} of {row['tickets']} tickets late)")
change = busiest["change_vs_prev_week"] or 0      # the first week has no "week before"
print(f"Busiest week: {busiest['week_start']} with {busiest['tickets']} tickets "
      f"({change:+d} vs the week before)")

# --- Write the same numbers as a Markdown file you can paste into a doc ---------
lines = [
    "# Weekly support report",
    "",
    f"Generated from `queries/weekly_sla_report.sql`. Data as of {REPORT_TIME}.",
    "",
    "| " + " | ".join(columns) + " |",
    "|" + "|".join(["---"] * len(columns)) + "|",
]
for row in rows:
    lines.append("| " + " | ".join("" if value is None else str(value) for value in row) + " |")
lines += [
    "",
    f"- Weeks below the {SLA_GOAL_PCT:.0f}% SLA goal: **{len(missed)} of {len(rows)}**",
    f"- Busiest week: **{busiest['week_start']}** ({busiest['tickets']} tickets)",
]

report_file = HERE / "output" / "weekly_sla_report.md"
report_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"\nSaved {report_file.relative_to(HERE.parent)}")
