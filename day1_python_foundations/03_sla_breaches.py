"""Day 1, example 3: find tickets that missed their first-response SLA.

Run it:   python day1_python_foundations/03_sla_breaches.py

Scenario: the SLA says a P1 ticket gets a first reply within 15 minutes.
Which tickets missed their target, and how bad is it per priority?

New ideas in this file:
  * JSON   - a settings file that Python reads straight into dicts
  * dates  - turning text into real date/time values you can subtract
  * a class - your first one, a tidy "Ticket" record (see the README)
"""

import csv
import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE.parent / "data"
OUTPUT_DIR = HERE / "output"


def parse_time(text):
    """'2026-10-14 09:24:26' -> a datetime. Empty text -> None (no value yet)."""
    if text == "":
        return None
    return datetime.strptime(text, "%Y-%m-%d %H:%M:%S")


# @dataclass turns a list of fields into a small class for you.
# A class is a template; each ticket built from it is an "object".
@dataclass
class Ticket:
    ticket_id: str
    priority: str
    category: str
    created_at: datetime
    first_response_at: datetime | None    # "datetime or nothing"

    # A method: a function that belongs to the object. "self" is this ticket.
    def response_minutes(self, now):
        """Minutes until the first reply. Still waiting? Count up to now."""
        answered = self.first_response_at or now
        return (answered - self.created_at).total_seconds() / 60


# --- Load the two files --------------------------------------------------------
policy = json.loads((DATA_DIR / "sla_policy.json").read_text(encoding="utf-8"))
targets = policy["targets"]                       # {"P1": {...}, "P2": {...}, ...}
now = parse_time(policy["report_time"])           # fixed "now" so results never change

tickets = []
with open(DATA_DIR / "tickets.csv", newline="", encoding="utf-8") as handle:
    for row in csv.DictReader(handle):
        tickets.append(Ticket(
            ticket_id=row["ticket_id"],
            priority=row["priority"],
            category=row["category"],
            created_at=parse_time(row["created_at"]),
            first_response_at=parse_time(row["first_response_at"]),
        ))

# --- Check every ticket against its target -------------------------------------
breaches = []
for ticket in tickets:
    target = targets[ticket.priority]["first_response_minutes"]
    waited = ticket.response_minutes(now)          # dot notation: ask the object
    if waited > target:
        breaches.append({
            "ticket_id": ticket.ticket_id,
            "priority": ticket.priority,
            "category": ticket.category,
            "created_at": ticket.created_at.isoformat(sep=" "),
            "waited_minutes": round(waited),
            "target_minutes": target,
            "times_over_target": round(waited / target, 1),
        })

# --- Report ---------------------------------------------------------------------
print(f"Checked {len(tickets)} tickets as of {now}")
print(f"First-response SLA breaches: {len(breaches)} ({len(breaches) / len(tickets):.1%})\n")

total_by_priority = Counter(ticket.priority for ticket in tickets)
breach_by_priority = Counter(row["priority"] for row in breaches)
print(f"{'Priority':<10}{'Target':>8}{'Tickets':>9}{'Breached':>10}{'Rate':>8}")
for priority in sorted(total_by_priority):
    total = total_by_priority[priority]
    late = breach_by_priority[priority]
    target = targets[priority]["first_response_minutes"]
    print(f"{priority:<10}{target:>6}m {total:>8}{late:>10}{late / total:>8.0%}")

worst = sorted(breaches, key=lambda row: row["times_over_target"], reverse=True)[:5]
print("\nFive worst breaches:")
for row in worst:
    print(f"  {row['ticket_id']}  {row['priority']}  {row['category']:<12}"
          f"waited {row['waited_minutes']:>5} min (target {row['target_minutes']}, "
          f"{row['times_over_target']}x over)")

# --- Save the full list so someone can open it in a spreadsheet -----------------
OUTPUT_DIR.mkdir(exist_ok=True)
output_file = OUTPUT_DIR / "sla_breaches.csv"
with open(output_file, "w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(breaches[0].keys()))
    writer.writeheader()
    writer.writerows(breaches)
print(f"\nSaved {len(breaches)} rows to {output_file.relative_to(HERE.parent)}")
