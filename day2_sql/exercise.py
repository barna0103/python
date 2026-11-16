"""Day 2 exercise: the agent leaderboard.

Run it:   python day2_sql/exercise.py

The support lead asks: "Per agent: how many tickets, how many escalated,
and the average satisfaction score? Sort the best score first, and leave
out anyone with fewer than 10 rated tickets."

The query below only lists the agents. Extend it (yourself, or by steering
an AI agent - see the prompts in the README). A finished version is in
solutions/exercise_solution.py.

You will need: JOIN tickets, GROUP BY, COUNT, SUM, AVG, HAVING, ORDER BY.
"""

from support_db import connect, show

QUERY = """
SELECT a.name, a.team
FROM agents AS a
ORDER BY a.name
"""

conn = connect()
show(conn, "Agent leaderboard (not finished yet)", QUERY)
conn.close()
