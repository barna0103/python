"""Day 3 exercise: how much did the outage hurt?

Run it:   python day3_data_analysis/exercise.py

On 2026-10-14 login was down for about two and a half hours. The VP of
Support asks: "Compared with a normal day, how did Login tickets from the
outage day do on reply time and satisfaction?"

The loading and the new columns are done. Fill in the TODO (yourself, or by
steering an AI agent - see the prompts in the README). A finished version
is in solutions/exercise_solution.py.
"""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUTAGE_DAY = "2026-10-14"

tickets = pd.read_csv(DATA_DIR / "tickets.csv",
                      parse_dates=["created_at", "first_response_at", "resolved_at"])

tickets["response_minutes"] = (
    tickets["first_response_at"] - tickets["created_at"]
).dt.total_seconds() / 60
tickets["day_type"] = "normal day"
tickets.loc[tickets["created_at"].dt.strftime("%Y-%m-%d") == OUTAGE_DAY, "day_type"] = "outage day"

login = tickets[tickets["category"] == "Login"]
print(f"{len(login)} Login tickets, {(login['day_type'] == 'outage day').sum()} from the outage day")

# TODO: build a table with one row per day_type ("normal day", "outage day")
# and these columns: number of tickets, median response_minutes, average csat,
# number of escalated tickets.
# Hint: 01_explore_tickets.py, step 6, does almost exactly this with
#       .groupby(...).agg(...)
comparison = None

if comparison is None:
    print("No comparison yet. Fill in the TODO, then run me again.")
else:
    print(comparison.to_string())
