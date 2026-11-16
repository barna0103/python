-- Weekly support report: volume, SLA compliance, satisfaction.
-- One row per week (Monday to Sunday).
--
-- :report_time is a named blank, filled in by 03_weekly_sla_report.py.
-- A ticket nobody has answered yet is measured up to the report time.

WITH ticket_sla AS (
    -- Step 1: one row per ticket, with its week and whether it was late.
    SELECT
        t.ticket_id,
        date(t.created_at, 'weekday 0', '-6 days') AS week_start,
        t.escalated,
        t.csat,
        CASE
            WHEN (julianday(COALESCE(t.first_response_at, :report_time))
                  - julianday(t.created_at)) * 24 * 60 > s.first_response_minutes
            THEN 1 ELSE 0
        END AS breached
    FROM tickets AS t
    JOIN sla_targets AS s ON s.priority = t.priority
),

weekly AS (
    -- Step 2: roll the tickets up into one row per week.
    SELECT
        week_start,
        COUNT(*)                                       AS tickets,
        SUM(escalated)                                 AS escalated,
        SUM(breached)                                  AS breached,
        ROUND(100.0 * (1 - AVG(breached)), 1)          AS sla_met_pct,
        ROUND(AVG(csat), 2)                            AS avg_csat
    FROM ticket_sla
    GROUP BY week_start
)

-- Step 3: compare each week with the one before it.
SELECT
    week_start,
    tickets,
    tickets - LAG(tickets) OVER (ORDER BY week_start) AS change_vs_prev_week,
    escalated,
    breached,
    sla_met_pct,
    avg_csat
FROM weekly
ORDER BY week_start;
