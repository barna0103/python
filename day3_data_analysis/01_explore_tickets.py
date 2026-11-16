"""Day 3, example 1: meet pandas - a spreadsheet you drive with code.

Run it:   python day3_data_analysis/01_explore_tickets.py

Scenario: you are handed a ticket export you have never seen. In five
minutes you want to know: how big, which columns, anything missing, and
what the obvious patterns are.

A DataFrame (df) is a table. A Series is one column of it.
"""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# One line to load. parse_dates turns the text columns into real timestamps.
tickets = pd.read_csv(
    DATA_DIR / "tickets.csv",
    parse_dates=["created_at", "first_response_at", "resolved_at"],
)

print("1. Size (rows, columns):", tickets.shape)

print("\n2. First rows - always look at the data before trusting it")
print(tickets.head(3).to_string(index=False))

print("\n3. Missing values per column (only columns that have any)")
missing = tickets.isna().sum()
print(missing[missing > 0].to_string())

print("\n4. Count values in one column")
print(tickets["priority"].value_counts().to_string())

print("\n5. Filter rows: unresolved P1 and P2 tickets")
urgent = tickets[(tickets["status"] != "resolved") & (tickets["priority"].isin(["P1", "P2"]))]
print(urgent[["ticket_id", "created_at", "priority", "category", "status"]].to_string(index=False))

print("\n6. Group and summarise: one row per category")
by_category = (
    tickets.groupby("category")
    .agg(
        tickets=("ticket_id", "count"),
        escalated=("escalated", "sum"),
        avg_csat=("csat", "mean"),
    )
    .round(2)
    .sort_values("avg_csat")
)
print(by_category.to_string())

print("\n7. Quick statistics for a number column")
print(tickets["csat"].describe().round(2).to_string())
