"""Day 2, example 2: the eight SQL patterns that answer most questions.

Run it:   python day2_sql/02_sql_basics.py

Each block prints the SQL and then the rows it returns. Read the SQL first,
predict the result, then check. Change a query and run again - you cannot
break anything, the database is rebuilt from the CSV files on demand.
"""

from support_db import connect, show

conn = connect()

show(conn, "1. SELECT: pick columns. LIMIT: only a few rows", """
SELECT ticket_id, priority, category, subject
FROM tickets
LIMIT 5
""")

show(conn, "2. WHERE: keep only rows that match", """
SELECT ticket_id, priority, status, subject
FROM tickets
WHERE status != 'resolved'
  AND priority IN ('P1', 'P2')
""")

show(conn, "3. ORDER BY: sort. Here, the newest escalated tickets first", """
SELECT ticket_id, created_at, priority, category
FROM tickets
WHERE escalated = 1
ORDER BY created_at DESC
LIMIT 5
""")

show(conn, "4. GROUP BY + COUNT: one row per group", """
SELECT category, COUNT(*) AS tickets
FROM tickets
GROUP BY category
ORDER BY tickets DESC
""")

show(conn, "5. Several summaries at once. AVG skips empty (NULL) scores", """
SELECT category,
       COUNT(*)            AS tickets,
       COUNT(csat)         AS rated,
       ROUND(AVG(csat), 2) AS avg_csat,
       SUM(escalated)      AS escalated
FROM tickets
GROUP BY category
ORDER BY avg_csat
""")

show(conn, "6. JOIN: look up the customer for each ticket", """
SELECT c.plan,
       COUNT(*)                       AS tickets,
       COUNT(DISTINCT t.customer_id)  AS customers,
       ROUND(AVG(t.csat), 2)          AS avg_csat
FROM tickets AS t
JOIN customers AS c ON c.customer_id = t.customer_id
GROUP BY c.plan
ORDER BY tickets DESC
""")

show(conn, "7. A calculated column: minutes until the first reply", """
SELECT t.priority,
       s.first_response_minutes AS target_minutes,
       ROUND(AVG((julianday(t.first_response_at) - julianday(t.created_at)) * 24 * 60), 1) AS avg_minutes
FROM tickets AS t
JOIN sla_targets AS s ON s.priority = t.priority
WHERE t.first_response_at IS NOT NULL
GROUP BY t.priority
""")

# The ? is a placeholder. The value is passed separately, never glued into the text.
show(conn, "8. A question with a blank to fill in (a parameter)", """
SELECT t.ticket_id, t.created_at, t.priority, t.status, t.subject
FROM tickets AS t
JOIN customers AS c ON c.customer_id = t.customer_id
WHERE c.name = ?
ORDER BY t.created_at DESC
LIMIT 5
""", ("Granite Bank",))

conn.close()
