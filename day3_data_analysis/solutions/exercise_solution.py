"""Day 3 exercise, one possible solution.

Run it:   python day3_data_analysis/solutions/exercise_solution.py
"""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
OUTAGE_DAY = "2026-10-14"

tickets = pd.read_csv(DATA_DIR / "tickets.csv",
                      parse_dates=["created_at", "first_response_at", "resolved_at"])

tickets["response_minutes"] = (
    tickets["first_response_at"] - tickets["created_at"]
).dt.total_seconds() / 60
tickets["day_type"] = "normal day"
tickets.loc[tickets["created_at"].dt.strftime("%Y-%m-%d") == OUTAGE_DAY, "day_type"] = "outage day"

login = tickets[tickets["category"] == "Login"]

comparison = login.groupby("day_type").agg(
    tickets=("ticket_id", "count"),
    median_response_min=("response_minutes", "median"),
    avg_csat=("csat", "mean"),
    escalated=("escalated", "sum"),
).round(1)

print("Login tickets: outage day vs normal days")
print(comparison.to_string())

normal, outage = comparison.loc["normal day"], comparison.loc["outage day"]
print(f"\nSatisfaction dropped from {normal['avg_csat']} to {outage['avg_csat']}.")
print(f"{outage['escalated']:.0f} of {outage['tickets']:.0f} outage tickets were escalated.")
print("Note: outage tickets were mostly P1/P2, so a short reply time is expected.")
print("A fair next step is to compare reply time against each ticket's SLA target.")
