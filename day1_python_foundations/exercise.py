"""Day 1 exercise: the escalation hot list.

Run it:   python day1_python_foundations/exercise.py

Your manager asks: "Which 5 customers had the most escalated tickets?
I need company name and plan, not customer ids."

The loading code is done. Fill in the two TODOs (yourself, or by steering
an AI agent - see the prompts in the README). A finished version is in
solutions/exercise_solution.py.
"""

import csv
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_rows(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


tickets = load_rows(DATA_DIR / "tickets.csv")
customers = load_rows(DATA_DIR / "customers.csv")

# A lookup table: customer_id -> the whole customer row.
customer_by_id = {row["customer_id"]: row for row in customers}

# TODO 1: count escalated tickets per customer_id.
# Hint: the "escalated" column holds the text "1" or "0".
# Hint: 02_ticket_counts.py counts things with Counter(...).
escalations = Counter()

# TODO 2: print the top 5 as "company name (plan): N escalated tickets".
# Hint: escalations.most_common(5) gives (customer_id, count) pairs.
# Hint: customer_by_id[customer_id]["name"] turns an id into a company name.

if not escalations:
    print("Nothing counted yet. Fill in TODO 1 and TODO 2, then run me again.")
