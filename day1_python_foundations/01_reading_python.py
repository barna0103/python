"""Day 1, example 1: a guided tour of the Python you will read most often.

Run it:   python day1_python_foundations/01_reading_python.py

Nothing to memorise. Read each block, guess what it prints, then check.
"""

# --- 1. Names point at values -------------------------------------------------
team = "Support"
open_tickets = 12
sla_target_minutes = 60.0
is_weekend = False
print("1.", team, open_tickets, sla_target_minutes, is_weekend)

# --- 2. A list is an ordered collection: [ ... ] ------------------------------
priorities = ["P1", "P2", "P3", "P4"]
print("2. first:", priorities[0], "| last:", priorities[-1], "| how many:", len(priorities))

# --- 3. A dict is a labelled record: { key: value } ---------------------------
# One ticket = one dict. This shape is everywhere: JSON, API replies, CSV rows.
ticket = {
    "ticket_id": "T0001",
    "priority": "P1",
    "category": "Login",
    "minutes_to_first_response": 22,
    "tags": ["sso", "outage"],          # a list inside a dict is normal
}
print("3.", ticket["ticket_id"], "is", ticket["priority"], "with tags", ticket["tags"])

# --- 4. A list of dicts is a table --------------------------------------------
tickets = [
    ticket,
    {"ticket_id": "T0002", "priority": "P3", "category": "Billing",
     "minutes_to_first_response": 95, "tags": []},
    {"ticket_id": "T0003", "priority": "P1", "category": "Login",
     "minutes_to_first_response": 9, "tags": ["sso"]},
]

# --- 5. Loop + condition: "for each row, if it matches, do something" ---------
print("5. P1 tickets:")
for row in tickets:
    if row["priority"] == "P1":
        print("   -", row["ticket_id"], row["category"])


# --- 6. A function is a named, reusable step ----------------------------------
# Read it as: "give me a ticket and a target, I give back True or False".
def breached_sla(row, target_minutes):
    return row["minutes_to_first_response"] > target_minutes


print("6. T0001 breached a 15 minute target?", breached_sla(tickets[0], 15))

# --- 7. A comprehension builds a new list in one line -------------------------
# Read it right to left: "for each row in tickets, if breached, keep its id".
late_ids = [row["ticket_id"] for row in tickets if breached_sla(row, 15)]
print("7. late tickets:", late_ids)

# --- 8. f-strings put values inside text --------------------------------------
share = len(late_ids) / len(tickets)
print(f"8. {len(late_ids)} of {len(tickets)} tickets were late ({share:.0%})")

# --- 9. Everything is an object: value.method() -------------------------------
# The dot means "ask this value to do something it knows how to do".
subject = "  Cannot log in after PASSWORD reset  "
print("9.", subject.strip().lower())           # text knows how to tidy itself
print("  ", "password" in subject.lower())        # "in" asks: is this inside that?
print("  ", ticket.get("assignee", "unassigned"))  # dicts know how to look up safely
