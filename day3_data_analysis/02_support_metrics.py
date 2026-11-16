"""Day 3, example 2: support metrics, a pivot table and a chart.

Run it:   python day3_data_analysis/02_support_metrics.py

Scenario: the quarterly business review is next week. Leadership asks:
  * Are we meeting the first-response SLA? For every plan?
  * Does a late reply really hurt satisfaction?
  * What did volume and SLA look like week by week?

The pattern to notice: load -> add columns -> join -> group -> chart.
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")           # draw to a file; no window needs to open
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE.parent / "data"
OUTPUT_DIR = HERE / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# --- Load ------------------------------------------------------------------------
tickets = pd.read_csv(DATA_DIR / "tickets.csv",
                      parse_dates=["created_at", "first_response_at", "resolved_at"])
customers = pd.read_csv(DATA_DIR / "customers.csv")
policy = json.loads((DATA_DIR / "sla_policy.json").read_text(encoding="utf-8"))
report_time = pd.Timestamp(policy["report_time"])

# A dict of dicts becomes a small table: one row per priority.
targets = pd.DataFrame(policy["targets"]).T.rename_axis("priority").reset_index()

# --- Add columns -----------------------------------------------------------------
# Whole-column maths: no loop needed. Unanswered tickets are measured up to now.
answered_at = tickets["first_response_at"].fillna(report_time)
tickets["response_minutes"] = (answered_at - tickets["created_at"]).dt.total_seconds() / 60
tickets["week"] = tickets["created_at"].dt.to_period("W").dt.start_time.dt.date

# --- Join (merge) ----------------------------------------------------------------
# Same idea as a SQL JOIN or a spreadsheet VLOOKUP.
tickets = tickets.merge(targets, on="priority").merge(customers, on="customer_id")
tickets["breached"] = tickets["response_minutes"] > tickets["first_response_minutes"]

print(f"Tickets: {len(tickets)} | SLA breaches: {tickets['breached'].sum()} "
      f"({tickets['breached'].mean():.1%})")

# --- Question 1: SLA by plan -------------------------------------------------------
by_plan = tickets.groupby("plan").agg(
    tickets=("ticket_id", "count"),
    median_response_min=("response_minutes", "median"),
    sla_met_pct=("breached", lambda late: 100 * (1 - late.mean())),
    avg_csat=("csat", "mean"),
).round(1)
print("\n1. SLA and satisfaction by plan")
print(by_plan.to_string())

# --- Question 2: does a late reply hurt satisfaction? ------------------------------
csat_by_breach = tickets.groupby("breached")["csat"].agg(["mean", "count"]).round(2)
csat_by_breach.index = ["answered in time", "answered late"]
print("\n2. Satisfaction: in time vs late")
print(csat_by_breach.to_string())

# --- Question 3: week by week, split by priority (a pivot table) -------------------
volume = tickets.pivot_table(index="week", columns="priority", values="ticket_id",
                             aggfunc="count", fill_value=0)
volume["total"] = volume.sum(axis=1)
print("\n3. Tickets per week and priority")
print(volume.to_string())

weekly = tickets.groupby("week").agg(
    tickets=("ticket_id", "count"),
    sla_met_pct=("breached", lambda late: 100 * (1 - late.mean())),
    avg_csat=("csat", "mean"),
).round(1)

# --- Chart -------------------------------------------------------------------------
figure, (top, bottom) = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
labels = [str(week)[5:] for week in weekly.index]          # "09-07" instead of "2026-09-07"

top.bar(labels, weekly["tickets"], color="#4C72B0")
top.set_title("Tickets created per week")
top.set_ylabel("tickets")

bottom.plot(labels, weekly["sla_met_pct"], marker="o", color="#C44E52")
bottom.axhline(85, linestyle="--", color="grey", label="goal: 85%")
bottom.set_title("First-response SLA met (%)")
bottom.set_ylabel("% in time")
bottom.set_xlabel("week starting (month-day)")
bottom.set_ylim(50, 100)
bottom.legend()

figure.tight_layout()
chart_file = OUTPUT_DIR / "weekly_support_metrics.png"
figure.savefig(chart_file, dpi=120)

summary_file = OUTPUT_DIR / "weekly_support_metrics.csv"
weekly.to_csv(summary_file)

print(f"\nSaved chart: {chart_file.relative_to(HERE.parent)}")
print(f"Saved table: {summary_file.relative_to(HERE.parent)}")
