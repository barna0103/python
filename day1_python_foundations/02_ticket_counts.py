"""Day 1, example 2: load a ticket export (CSV) and answer quick questions.

Run it:   python day1_python_foundations/02_ticket_counts.py

Scenario: your manager asks "what does the ticket queue look like?" and you
have a CSV export from the helpdesk tool. No spreadsheet needed.
"""

import csv
from collections import Counter
from pathlib import Path

# Path(__file__) is this file. Going up two levels gives the repo folder,
# so the script works no matter which folder you run it from.
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_rows(csv_path):
    """Read a CSV file into a list of dicts (one dict per row)."""
    with open(csv_path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def print_counts(title, counter, top=None):
    print(f"\n{title}")
    for value, count in counter.most_common(top):
        print(f"  {value:<12} {count:>4}")


tickets = load_rows(DATA_DIR / "tickets.csv")
print(f"Loaded {len(tickets)} tickets. Columns: {', '.join(tickets[0].keys())}")

# Counter does "group and count" for you.
print_counts("Tickets by priority", Counter(row["priority"] for row in tickets))
print_counts("Tickets by category", Counter(row["category"] for row in tickets))
print_counts("Tickets by status", Counter(row["status"] for row in tickets))

# Filter first, then count: only tickets that are not resolved yet.
not_resolved = [row for row in tickets if row["status"] != "resolved"]
print_counts("Unresolved tickets by priority", Counter(row["priority"] for row in not_resolved))

# created_at looks like "2026-10-14 09:24:26". The first 10 characters are the date.
per_day = Counter(row["created_at"][:10] for row in tickets)
print_counts("Three busiest days", per_day, top=3)

# CSV values are always text. Convert before doing maths.
scores = [int(row["csat"]) for row in tickets if row["csat"] != ""]
print(f"\nAverage satisfaction: {sum(scores) / len(scores):.2f} out of 5 "
      f"({len(scores)} of {len(tickets)} tickets were rated)")
