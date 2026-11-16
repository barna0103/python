"""Day 5, example 3 (capstone): a weekly report where code does the maths
and the LLM does the writing.

Run it:   python day5_llm_agents/03_weekly_report_pipeline.py
          python day5_llm_agents/03_weekly_report_pipeline.py --week 2026-10-12   (the outage week)

Scenario: every Monday you send leadership a short support update. The
numbers must be right; the wording takes you 30 minutes. Split the job:

    1. pandas computes the metrics        (exact, repeatable - Day 3)
    2. the LLM turns them into a summary  (the only "AI" step)
    3. code checks the summary's numbers  (trust, but verify)
    4. a draft report is saved            (a person reviews before sending)

This is a WORKFLOW: fixed steps, decided by you. Compare with example 2,
an AGENT, where the model decides the steps. Prefer a workflow whenever
you already know the steps - it is cheaper, faster and easier to check.
"""

import argparse
import json
import re
from pathlib import Path

import pandas as pd

from llm import get_llm

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE.parent / "data"
SLA_GOAL_PCT = 85

parser = argparse.ArgumentParser(description="Draft the weekly support report.")
parser.add_argument("--week", default="2026-10-26",
                    help="Monday of the week to report on, YYYY-MM-DD (default: 2026-10-26)")
args = parser.parse_args()

# --- Step 1: metrics with pandas ---------------------------------------------------------
tickets = pd.read_csv(DATA_DIR / "tickets.csv",
                      parse_dates=["created_at", "first_response_at", "resolved_at"])
customers = pd.read_csv(DATA_DIR / "customers.csv").rename(columns={"name": "customer"})
policy = json.loads((DATA_DIR / "sla_policy.json").read_text(encoding="utf-8"))
report_time = pd.Timestamp(policy["report_time"])
targets = pd.DataFrame(policy["targets"]).T.rename_axis("priority").reset_index()

tickets = tickets.merge(targets, on="priority").merge(customers, on="customer_id")
answered_at = tickets["first_response_at"].fillna(report_time)
tickets["response_minutes"] = (answered_at - tickets["created_at"]).dt.total_seconds() / 60
tickets["breached"] = tickets["response_minutes"] > tickets["first_response_minutes"]
tickets["week"] = tickets["created_at"].dt.to_period("W").dt.start_time


def week_numbers(week_start):
    """The headline numbers for one week, as plain Python values."""
    week = tickets[tickets["week"] == week_start]
    if week.empty:
        raise SystemExit(f"No tickets found for the week starting {week_start.date()}. "
                         "Use a Monday between 2026-09-14 and 2026-10-26.")
    return {
        "tickets": int(len(week)),
        "escalated": int(week["escalated"].sum()),
        "sla_met_pct": round(float(100 * (1 - week["breached"].mean())), 1),
        "avg_csat": round(float(week["csat"].mean()), 2),
    }


this_week = pd.Timestamp(args.week)
previous_week = this_week - pd.Timedelta(days=7)
in_week = tickets[tickets["week"] == this_week]

top_categories = in_week["category"].value_counts().head(3)
urgent = tickets[(tickets["status"] != "resolved") & (tickets["priority"].isin(["P1", "P2"]))
                 & (tickets["created_at"] < this_week + pd.Timedelta(days=7))].copy()
urgent["age_days"] = (report_time - urgent["created_at"]).dt.days
urgent = urgent.sort_values("age_days", ascending=False)

metrics = {
    "week_start": args.week,
    "sla_goal_pct": SLA_GOAL_PCT,
    "this_week": week_numbers(this_week),
    "previous_week": week_numbers(previous_week),
    "top_categories": [{"category": name, "tickets": int(count)}
                       for name, count in top_categories.items()],
    "unresolved_urgent_count": int(len(urgent)),
    "unresolved_urgent": urgent[["ticket_id", "priority", "customer", "plan", "age_days"]]
                         .to_dict("records"),
}
print("Step 1 - metrics computed by pandas:")
for key in ["this_week", "previous_week", "top_categories", "unresolved_urgent_count"]:
    print(f"  {key}: {metrics[key]}")

# --- Step 2: the LLM writes the summary --------------------------------------------------
SYSTEM_PROMPT = """You write the weekly support update for company leadership.
Write exactly 4 short bullet points: volume, SLA, satisfaction, what to watch.
Use only numbers that appear in the metrics. Do not calculate or estimate new numbers.
Plain language. No greeting, no sign-off."""

prompt = f"Write this week's update from these metrics.\n<metrics>\n{json.dumps(metrics, indent=2)}\n</metrics>"

print("\nStep 2 - asking the LLM for a summary")
llm = get_llm()
summary = llm.ask(SYSTEM_PROMPT, prompt).strip()
print(summary)

# --- Step 3: check the LLM's numbers against ours ----------------------------------------
# Every number in the summary should be one we gave it. Anything else is a red flag.
# This is a cheap check, not proof: it catches invented numbers, not wrong wording.
known_numbers = set(re.findall(r"\d+(?:\.\d+)?", json.dumps(metrics)))
used_numbers = re.findall(r"\d+(?:\.\d+)?", summary)
unknown = sorted({number for number in used_numbers if number not in known_numbers})

print("\nStep 3 - checking the summary")
if unknown:
    status = f"NEEDS REVIEW - numbers not found in the metrics: {', '.join(unknown)}"
else:
    status = "numbers check passed - every number in the summary comes from the metrics"
print(" ", status)

# --- Step 4: save a draft for a person to review -----------------------------------------
lines = [
    f"# Weekly support update - week of {args.week}",
    "",
    f"> DRAFT. Summary written by: {llm.name}. Check: {status}.",
    "> Review before sending.",
    "",
    "## Summary",
    "",
    summary,
    "",
    "## Numbers",
    "",
    "| Metric | This week | Previous week |",
    "|---|---|---|",
]
labels = {"tickets": "Tickets created", "escalated": "Escalated",
          "sla_met_pct": "First-response SLA met (%)", "avg_csat": "Average CSAT"}
for key, label in labels.items():
    lines.append(f"| {label} | {metrics['this_week'][key]} | {metrics['previous_week'][key]} |")

lines += ["", "## Unresolved P1/P2 tickets", "",
          "| Ticket | Priority | Customer | Plan | Age (days) |", "|---|---|---|---|---|"]
for item in metrics["unresolved_urgent"]:
    lines.append(f"| {item['ticket_id']} | {item['priority']} | {item['customer']} "
                 f"| {item['plan']} | {item['age_days']} |")

report_file = HERE / "output" / f"weekly_report_{args.week}.md"
report_file.parent.mkdir(exist_ok=True)
report_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"\nStep 4 - saved draft: {report_file.relative_to(HERE.parent)}")
