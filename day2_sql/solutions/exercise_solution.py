"""Day 2 exercise, one possible solution.

Run it:   python day2_sql/solutions/exercise_solution.py
"""

import sys
from pathlib import Path

# support_db.py lives one folder up, so tell Python to look there too.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from support_db import connect, show  # noqa: E402

QUERY = """
SELECT a.name,
       a.team,
       COUNT(*)              AS tickets,
       SUM(t.escalated)      AS escalated,
       COUNT(t.csat)         AS rated,
       ROUND(AVG(t.csat), 2) AS avg_csat
FROM agents AS a
JOIN tickets AS t ON t.agent_id = a.agent_id
GROUP BY a.agent_id
HAVING COUNT(t.csat) >= 10
ORDER BY avg_csat DESC
"""

conn = connect()
show(conn, "Agent leaderboard", QUERY)
conn.close()

print("\nRead it with care. Agents handle different mixes of tickets (Tier 2 takes")
print("the escalations), and one agent is missing because he has fewer than 10")
print("rated tickets. A ranking is a starting point for questions, not a verdict.")
