"""Day 1 exercise, one possible solution.

Run it:   python day1_python_foundations/solutions/exercise_solution.py
"""

import csv
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def load_rows(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


tickets = load_rows(DATA_DIR / "tickets.csv")
customers = load_rows(DATA_DIR / "customers.csv")
customer_by_id = {row["customer_id"]: row for row in customers}

escalations = Counter(row["customer_id"] for row in tickets if row["escalated"] == "1")

print("Escalation hot list (top 5 customers):")
for customer_id, count in escalations.most_common(5):
    customer = customer_by_id[customer_id]
    print(f"  {customer['name']} ({customer['plan']}): {count} escalated tickets")

total = sum(escalations.values())
print(f"\n{total} escalated tickets across {len(escalations)} customers.")
