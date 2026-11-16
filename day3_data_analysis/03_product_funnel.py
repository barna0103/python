"""Day 3, example 3: a product funnel from raw event data.

Run it:   python day3_data_analysis/03_product_funnel.py

Scenario: you are the product manager for onboarding. New users should
sign up -> create a project -> invite a teammate -> export a report.
Where do they drop off, and is it different per plan?

The data is an "event log": one row each time a user does something.
Most product analytics starts from a table shaped like this.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE.parent / "data"
OUTPUT_DIR = HERE / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

FUNNEL_STEPS = ["signup", "project_created", "teammate_invited", "report_exported"]

events = pd.read_csv(DATA_DIR / "product_events.csv", parse_dates=["event_time"])
customers = pd.read_csv(DATA_DIR / "customers.csv")
events = events.merge(customers[["customer_id", "plan"]], on="customer_id")

print(f"{len(events)} events from {events['user_id'].nunique()} users "
      f"at {events['customer_id'].nunique()} companies")
print(events.head(4).to_string(index=False))

# --- The funnel: how many different users reached each step? -----------------------
users_per_step = events.groupby("event_name")["user_id"].nunique().reindex(FUNNEL_STEPS)

funnel = pd.DataFrame({"users": users_per_step})
funnel["pct_of_signups"] = (100 * funnel["users"] / funnel["users"].iloc[0]).round(1)
funnel["pct_of_previous_step"] = (100 * funnel["users"] / funnel["users"].shift(1)).round(1)
print("\n1. Onboarding funnel (all users)")
print(funnel.to_string())

biggest_drop = funnel["pct_of_previous_step"].idxmin()
print(f"\n   Biggest drop-off is at: {biggest_drop} "
      f"(only {funnel.loc[biggest_drop, 'pct_of_previous_step']}% of the previous step)")

# --- Same funnel, split by plan ------------------------------------------------------
by_plan = (
    events.groupby(["plan", "event_name"])["user_id"].nunique()
    .unstack("event_name")[FUNNEL_STEPS]
)
by_plan_pct = by_plan.div(by_plan["signup"], axis=0).mul(100).round(1)
print("\n2. Users reaching each step, by plan")
print(by_plan.to_string())
print("\n3. The same as % of signups")
print(by_plan_pct.to_string())

# --- Weekly active users: people who exported at least one report that week --------
exports = events[events["event_name"] == "report_exported"].copy()
exports["week"] = exports["event_time"].dt.to_period("W").dt.start_time.dt.date
weekly_active = exports.groupby("week")["user_id"].nunique()
print("\n4. Users exporting a report, per week")
print(weekly_active.to_string())

# --- Chart -----------------------------------------------------------------------------
figure, (left, right) = plt.subplots(1, 2, figsize=(11, 4.5))

left.barh(FUNNEL_STEPS[::-1], funnel["users"][::-1], color="#4C72B0")
for step, users, pct in zip(FUNNEL_STEPS, funnel["users"], funnel["pct_of_signups"]):
    left.text(users + 2, step, f"{users} ({pct:.0f}%)", va="center")
left.set_xlim(0, funnel["users"].max() * 1.25)
left.set_title("Onboarding funnel: users reaching each step")

by_plan_pct.T.plot(kind="bar", ax=right, rot=20)
right.set_title("% of signups reaching each step, by plan")
right.set_xlabel("")
right.set_ylabel("% of signups")

figure.tight_layout()
chart_file = OUTPUT_DIR / "product_funnel.png"
figure.savefig(chart_file, dpi=120)
print(f"\nSaved chart: {chart_file.relative_to(HERE.parent)}")
