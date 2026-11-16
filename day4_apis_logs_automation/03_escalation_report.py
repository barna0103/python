"""Day 4, example 3: an automated escalation report.

Run it:   python day4_apis_logs_automation/03_escalation_report.py
          python day4_apis_logs_automation/03_escalation_report.py --min-age-days 14
          python day4_apis_logs_automation/03_escalation_report.py --post-comments

Scenario: every morning the escalation manager wants one page:
which urgent tickets are still unresolved, how old, for which customers,
and what the logs say about the last incident.

Pipeline:  API (tickets) + log file (incident)  ->  Markdown report
With --post-comments it also adds an internal note to each stale ticket.
Without that flag it only prints what it WOULD post (a "dry run").
"""

import argparse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from helpdesk_client import connect_to_helpdesk
from log_tools import find_incident, read_log

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE.parent / "data"
REPORT_TIME = datetime(2026, 11, 2, 9, 0, tzinfo=timezone.utc)   # fixed "now" for the course

# --- Command line options: the knobs someone can turn without editing code ------------
parser = argparse.ArgumentParser(description="Build the daily escalation report.")
parser.add_argument("--min-age-days", type=int, default=7,
                    help="a ticket this old (in days) counts as stale (default: 7)")
parser.add_argument("--post-comments", action="store_true",
                    help="really post internal notes on stale tickets (default: dry run)")
args = parser.parse_args()

# --- 1. Fetch: unresolved P1 and P2 tickets from the API --------------------------------
client = connect_to_helpdesk()
tickets = client.list_tickets(status="open,pending", priority="P1,P2")

for ticket in tickets:
    created = datetime.fromisoformat(ticket["created_at"])
    ticket["age_days"] = (REPORT_TIME - created).days
tickets.sort(key=lambda ticket: ticket["age_days"], reverse=True)
stale = [ticket for ticket in tickets if ticket["age_days"] >= args.min_age_days]

# --- 2. Enrich: what do the logs say about the last incident? ---------------------------
entries, _ = read_log(DATA_DIR / "app.log")
incident = find_incident(entries)

# --- 3. Build the report text ------------------------------------------------------------
by_plan = Counter(ticket["customer"]["plan"] for ticket in tickets)
lines = [
    "# Daily escalation report",
    "",
    f"Report time: {REPORT_TIME:%Y-%m-%d %H:%M} UTC",
    "",
    "## Summary",
    "",
    f"- Unresolved P1/P2 tickets: **{len(tickets)}**",
    f"- Stale ({args.min_age_days}+ days old): **{len(stale)}**",
    "- By plan: " + ", ".join(f"{plan} {count}" for plan, count in by_plan.most_common()),
    "",
    "## Unresolved P1/P2 tickets (oldest first)",
    "",
    "| Ticket | Priority | Age (days) | Customer | Plan | Assignee | Subject |",
    "|---|---|---|---|---|---|---|",
]
for ticket in tickets:
    lines.append(
        f"| {ticket['id']} | {ticket['priority']} | {ticket['age_days']} "
        f"| {ticket['customer']['name']} | {ticket['customer']['plan']} "
        f"| {ticket['assignee']['name']} | {ticket['subject']} |"
    )

lines += ["", "## Last incident seen in the logs", ""]
if incident is None:
    lines.append("No error spike found in the log file.")
else:
    lines += [
        f"- Window: {incident['start']:%Y-%m-%d %H:%M} to {incident['end']:%H:%M} UTC "
        f"({incident['minutes']} minutes)",
        f"- Errors: {incident['error_count']}, customers affected: {incident['customers_affected']}",
        f"- Main error: \"{incident['top_messages'][0][0]}\"",
    ]
    incident_day = incident["start"].strftime("%Y-%m-%d")
    linked = [t for t in tickets if t["created_at"].startswith(incident_day)]
    lines.append(f"- Unresolved P1/P2 tickets opened that day: **{len(linked)}**")

report_file = HERE / "output" / "escalation_report.md"
report_file.parent.mkdir(exist_ok=True)
report_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

print("\n".join(lines[:9]))
print(f"\nSaved the full report to {report_file.relative_to(HERE.parent)}")

# --- 4. Act: nudge the owners of stale tickets (only when asked to) ---------------------
print(f"\nStale tickets: {len(stale)}")
for ticket in stale:
    note = (f"Automated reminder: this {ticket['priority']} ticket has been unresolved for "
            f"{ticket['age_days']} days. Please post an update for {ticket['customer']['name']}.")
    if args.post_comments:
        comment = client.add_comment(ticket["id"], note)
        print(f"  posted comment #{comment['id']} on {ticket['id']}")
    else:
        print(f"  [dry run] would comment on {ticket['id']}: {note}")
if stale and not args.post_comments:
    print("Nothing was posted. Re-run with --post-comments to post for real.")
