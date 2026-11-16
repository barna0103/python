"""Day 4 exercise, one possible solution.

Run it:   python day4_apis_logs_automation/solutions/exercise_solution.py
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

# helpdesk_client.py lives one folder up, so tell Python to look there too.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from helpdesk_client import connect_to_helpdesk  # noqa: E402

REPORT_TIME = datetime(2026, 11, 2, 9, 0, tzinfo=timezone.utc)

client = connect_to_helpdesk()
tickets = client.list_tickets(status="open,pending")

enterprise = [ticket for ticket in tickets if ticket["customer"]["plan"] == "Enterprise"]

for ticket in enterprise:
    created = datetime.fromisoformat(ticket["created_at"])
    ticket["age_days"] = (REPORT_TIME - created).days
enterprise.sort(key=lambda ticket: ticket["age_days"], reverse=True)

print(f"\n{len(enterprise)} unresolved tickets for Enterprise customers (oldest first):")
for ticket in enterprise:
    print(f"  {ticket['id']}  {ticket['priority']}  {ticket['age_days']:>2} days  "
          f"{ticket['customer']['name']:<16} {ticket['assignee']['name']:<14} {ticket['subject']}")

waiting = {ticket["customer"]["name"] for ticket in enterprise}
print(f"\nCustomers to call: {', '.join(sorted(waiting))}")
