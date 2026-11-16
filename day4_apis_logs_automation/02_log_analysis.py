"""Day 4, example 2: find an incident in a log file and tie it to tickets.

Run it:   python day4_apis_logs_automation/02_log_analysis.py

Scenario: it is the morning after 14 October. Customers say "login was
down". Engineering asks support: when exactly, which service, how many
customers? The answer is in data/app.log - about 1,000 lines nobody wants
to read by hand.
"""

import csv
from collections import Counter
from pathlib import Path

from log_tools import find_incident, parse_line, read_log

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
LOG_FILE = DATA_DIR / "app.log"

# --- 1. From a line of text to a dict you can work with -------------------------------
first_line = LOG_FILE.read_text(encoding="utf-8").splitlines()[0]
print("1. One raw line:")
print("  ", first_line)
print("   Parsed into named pieces:")
for key, value in parse_line(first_line).items():
    print(f"     {key:<12} {value}")

# --- 2. Parse the whole file -----------------------------------------------------------
entries, skipped = read_log(LOG_FILE)
print(f"\n2. Parsed {len(entries)} lines ({skipped} could not be parsed)")
print("   Lines per level:", dict(Counter(entry["level"] for entry in entries)))

# --- 3. Compare the two days -----------------------------------------------------------
errors = [entry for entry in entries if entry["level"] == "ERROR"]
per_day = Counter(entry["time"].strftime("%Y-%m-%d") for entry in errors)
print("\n3. ERROR lines per day:")
for day, count in sorted(per_day.items()):
    print(f"   {day}  {count:>4}")

# --- 4. Find the incident window automatically -----------------------------------------
incident = find_incident(entries)
print("\n4. Incident window (10-minute buckets with 5 or more errors):")
print(f"   from {incident['start']} to {incident['end']} ({incident['minutes']} minutes)")
print(f"   {incident['error_count']} errors, {incident['customers_affected']} customers affected")
print("   Services:", ", ".join(f"{name} ({count})" for name, count in incident["services"]))
print("   Top error messages:")
for message, count in incident["top_messages"]:
    print(f"     {count:>4}  {message}")

# --- 5. Line it up with the support queue ----------------------------------------------
incident_day = incident["start"].strftime("%Y-%m-%d")
errors_per_hour = Counter(entry["time"].hour for entry in errors
                          if entry["time"].strftime("%Y-%m-%d") == incident_day)

with open(DATA_DIR / "tickets.csv", newline="", encoding="utf-8") as handle:
    login_per_hour = Counter(
        int(row["created_at"][11:13])
        for row in csv.DictReader(handle)
        if row["category"] == "Login" and row["created_at"].startswith(incident_day)
    )

print(f"\n5. {incident_day}, hour by hour (UTC): log errors vs new Login tickets")
print("   hour  errors  tickets")
for hour in range(7, 16):
    print(f"   {hour:02d}:00 {errors_per_hour[hour]:>6} {login_per_hour[hour]:>8}  "
          f"{'#' * login_per_hour[hour]}")
print("   Errors start first; tickets follow and keep coming after the fix.")
