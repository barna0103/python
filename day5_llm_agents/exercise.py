"""Day 5 exercise: add a guardrail and prove it with checks.

Run it:   python day5_llm_agents/exercise.py

Finance says: "The agent must never show customer revenue (the mrr_usd
column in the customers table)." Today nothing stops it.

Your job: make guarded_run_sql refuse those queries until every check
below says PASS. No LLM is needed - a guardrail is ordinary code, which
is exactly why you can trust it more than a sentence in a prompt.

Fill in the TODO (yourself, or by steering an AI agent - see the prompts
in the README). A finished version is in solutions/exercise_solution.py.
"""

from support_tools import run_sql


def guarded_run_sql(query):
    """run_sql plus one extra rule: customer revenue is confidential."""
    # TODO: return a text starting with "REFUSED:" when the query would
    #       reveal mrr_usd. Think about two ways a query can do that:
    #         1. it names the column:            SELECT name, mrr_usd FROM customers
    #         2. it asks for every column:       SELECT * FROM customers
    return run_sql(query)


# (description, query, what should happen)
CHECKS = [
    ("a normal question still works", "SELECT COUNT(*) FROM tickets", "allowed"),
    ("customer names still work", "SELECT name, plan FROM customers LIMIT 3", "allowed"),
    ("naming the revenue column", "SELECT name, mrr_usd FROM customers", "refused"),
    ("upper case does not sneak through", "SELECT SUM(MRR_USD) FROM customers", "refused"),
    ("SELECT * on customers", "SELECT * FROM customers", "refused"),
    ("changing data (already blocked)", "DELETE FROM tickets", "refused"),
]

passed = 0
for description, query, expected in CHECKS:
    output = guarded_run_sql(query)
    actual = "refused" if output.startswith("REFUSED") else "allowed"
    ok = actual == expected
    passed += ok
    print(f"{'PASS' if ok else 'FAIL'}  {description:<36} expected {expected:<8} got {actual}")

print(f"\n{passed} of {len(CHECKS)} checks pass.")
if passed < len(CHECKS):
    print("Not done yet: change guarded_run_sql until every line says PASS.")
else:
    print("All checks pass. The guardrail works for these cases.")
