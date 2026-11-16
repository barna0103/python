"""Day 5 exercise, one possible solution.

Run it:   python day5_llm_agents/solutions/exercise_solution.py
"""

import sys
from pathlib import Path

# support_tools.py lives one folder up, so tell Python to look there too.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from support_tools import run_sql  # noqa: E402


def guarded_run_sql(query):
    """run_sql plus one extra rule: customer revenue is confidential."""
    text = query.lower()
    if "mrr_usd" in text:
        return "REFUSED: customer revenue (mrr_usd) is confidential."
    # "*" pulls in every column, so it would include mrr_usd without naming it.
    # COUNT(*) is fine: it counts rows and shows no columns, so ignore it first.
    without_count = text.replace("count(*)", "")
    if "customers" in text and "*" in without_count:
        return "REFUSED: name the columns you need from customers instead of using *."
    return run_sql(query)


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
print("\nA text filter like this is easy to get around with clever SQL. The stronger")
print("fix: do not load mrr_usd into the agent's database at all (see build_database")
print("in support_tools.py). An agent cannot leak what it was never given.")
