"""Day 4 exercise: who is waiting on us?

Run it:   python day4_apis_logs_automation/exercise.py

The account management team asks: "Which Enterprise customers have
unresolved tickets right now? Oldest first, with the age in days and who
it is assigned to."

Fetching is done. Fill in the two TODOs (yourself, or by steering an AI
agent - see the prompts in the README). A finished version is in
solutions/exercise_solution.py.
"""

from datetime import datetime, timezone

from helpdesk_client import connect_to_helpdesk

REPORT_TIME = datetime(2026, 11, 2, 9, 0, tzinfo=timezone.utc)

client = connect_to_helpdesk()
tickets = client.list_tickets(status="open,pending")
print(f"Fetched {len(tickets)} unresolved tickets from the API")

# Each ticket is a nested dict. Print one to see its shape:
example = tickets[0]
print("Example:", example["id"], "|", example["customer"], "|", example["created_at"])

# TODO 1: keep only tickets whose customer is on the "Enterprise" plan.
# Hint: the plan is nested: ticket["customer"]["plan"]
enterprise = []

# TODO 2: for each of those, work out the age in days, sort oldest first and print
#         ticket id, age, customer name, assignee name and subject.
# Hint: 03_escalation_report.py computes "age_days" from created_at and sorts by it.

if not enterprise:
    print("No Enterprise list yet. Fill in TODO 1 and TODO 2, then run me again.")
