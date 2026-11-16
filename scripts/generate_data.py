"""Generate the sample data used by every day of the course.

You do NOT need to run this. The files in data/ are already committed.
It is here so you can see where the data came from, or ask an AI agent to
change it (more customers, a second incident, a new ticket category ...).

    python scripts/generate_data.py

The data is fictional: a small SaaS company called "Northbeam" that sells a
project reporting tool. The random seed is fixed, so every run produces
exactly the same files.

Things deliberately hidden in the data for you to find during the course:
  * a login outage on 2026-10-14 (ticket spike + error spike in the log)
  * Enterprise customers get faster first responses than Free customers
  * tickets that breach their SLA get worse satisfaction scores
  * the biggest drop-off in the product funnel is inviting a teammate
"""

import csv
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SEED = 7

FIRST_DAY = datetime(2026, 9, 7)          # a Monday
NUMBER_OF_DAYS = 56                       # 8 full weeks, ends Sunday 2026-11-01
REPORT_TIME = datetime(2026, 11, 2, 9, 0)  # "now" for every script in the course
INCIDENT_START = datetime(2026, 10, 14, 9, 10)
INCIDENT_END = datetime(2026, 10, 14, 11, 40)

# SLA targets. The same numbers are written to data/sla_policy.json.
SLA_POLICY = {
    "P1": {"first_response_minutes": 15, "resolution_hours": 4},
    "P2": {"first_response_minutes": 60, "resolution_hours": 24},
    "P3": {"first_response_minutes": 240, "resolution_hours": 72},
    "P4": {"first_response_minutes": 480, "resolution_hours": 120},
}

COMPANY_NAMES = [
    "Alder Logistics", "Birchwood Health", "Cobalt Retail", "Dune Analytics",
    "Elm Street Media", "Fjord Shipping", "Granite Bank", "Harbor Foods",
    "Indigo Travel", "Juniper Labs", "Kestrel Energy", "Lakeside Schools",
    "Maple Robotics", "Nimbus Insurance", "Orchard Pharma", "Pinecone Games",
    "Quartz Telecom", "Riverbend Legal", "Saffron Hotels", "Tundra Outdoors",
    "Umber Design", "Vista Airlines", "Willow Books", "Xenon Motors",
    "Yarrow Farms", "Zephyr Fitness", "Amber Studios", "Basalt Mining",
    "Cedar Finance", "Delta Couriers", "Ember Security", "Flint Hardware",
    "Glacier Water", "Heron Consulting", "Iris Cosmetics", "Jade Electronics",
    "Kelp Biotech", "Lotus Wellness", "Moss Architecture", "Nectar Beverages",
]

AGENTS = [
    ("A01", "Priya Nair", "Tier 1"),
    ("A02", "Marco Rossi", "Tier 1"),
    ("A03", "Chen Wei", "Tier 1"),
    ("A04", "Sofia Alvarez", "Tier 1"),
    ("A05", "Tom Becker", "Tier 2"),
    ("A06", "Amara Okafor", "Tier 2"),
    ("A07", "Lena Novak", "Tier 2"),
    ("A08", "David Kim", "Escalations"),
]

SUBJECTS = {
    "Login": [
        "Cannot log in after password reset",
        "SSO login loops back to sign-in page",
        "Two-factor code never arrives",
        "Account locked after too many attempts",
    ],
    "Billing": [
        "Charged twice this month",
        "Need invoice with VAT number",
        "Plan upgrade did not apply",
        "Refund request for unused seats",
    ],
    "Performance": [
        "Dashboard takes over 30 seconds to load",
        "Report export times out",
        "App is slow every morning",
    ],
    "Bug": [
        "Chart shows wrong totals",
        "Export to PDF cuts off last column",
        "Filters reset when I change page",
        "Duplicate rows in weekly report",
    ],
    "How-to": [
        "How do I share a report with a client?",
        "How to schedule a weekly email report",
        "Where can I change the date format?",
        "How do I add a teammate?",
    ],
    "Integration": [
        "Slack integration stopped posting",
        "Salesforce sync is missing records",
        "API returns 401 with a valid token",
        "Webhook deliveries are delayed",
    ],
}
CATEGORY_WEIGHTS = {
    "Login": 14, "Billing": 16, "Performance": 12,
    "Bug": 22, "How-to": 22, "Integration": 14,
}
# Chance of P1, P2, P3, P4 per category: a how-to question is rarely urgent.
PRIORITY_WEIGHTS = {
    "Login": [8, 25, 50, 17],
    "Billing": [2, 15, 50, 33],
    "Performance": [6, 22, 50, 22],
    "Bug": [4, 16, 55, 25],
    "How-to": [0, 3, 45, 52],
    "Integration": [5, 20, 50, 25],
}
INCIDENT_SUBJECTS = [
    "Cannot log in - error 503",
    "Login page shows 'service unavailable'",
    "Whole team locked out since this morning",
    "SSO login fails with timeout",
]


def clock(moment):
    """Format a datetime the way the CSV files store it."""
    return moment.strftime("%Y-%m-%d %H:%M:%S")


def weighted_choice(rng, weights):
    names = list(weights)
    return rng.choices(names, weights=[weights[name] for name in names])[0]


def make_customers(rng):
    plans = ["Free"] * 14 + ["Pro"] * 16 + ["Enterprise"] * 10
    rng.shuffle(plans)
    customers = []
    for number, name in enumerate(COMPANY_NAMES, start=1):
        plan = plans[number - 1]
        if plan == "Free":
            mrr = 0
        elif plan == "Pro":
            mrr = rng.choice([99, 199, 299, 499])
        else:
            mrr = rng.choice([2000, 3500, 5000, 8000])
        signup = FIRST_DAY - timedelta(days=rng.randint(30, 700))
        customers.append({
            "customer_id": f"C{number:03d}",
            "name": name,
            "plan": plan,
            "region": rng.choice(["EMEA", "AMER", "APAC"]),
            "signup_date": signup.strftime("%Y-%m-%d"),
            "mrr_usd": mrr,
        })
    return customers


def make_ticket(rng, ticket_number, created, customer, incident=False):
    if incident:
        category = "Login"
        priority = rng.choices(["P1", "P2"], weights=[45, 55])[0]
        subject = rng.choice(INCIDENT_SUBJECTS)
    else:
        category = weighted_choice(rng, CATEGORY_WEIGHTS)
        priority = rng.choices(["P1", "P2", "P3", "P4"], weights=PRIORITY_WEIGHTS[category])[0]
        subject = rng.choice(SUBJECTS[category])

    targets = SLA_POLICY[priority]

    # How fast did we answer? Usually well inside the target, sometimes not.
    speed = {"Enterprise": 0.40, "Pro": 0.55, "Free": 0.80}[customer["plan"]]
    if incident:
        speed *= 2.2  # everyone is swamped during an outage
    response_minutes = targets["first_response_minutes"] * speed * rng.lognormvariate(0, 0.6)
    response_minutes = max(1.0, response_minutes)
    first_response = created + timedelta(minutes=response_minutes)

    resolve_hours = targets["resolution_hours"] * 0.55 * rng.lognormvariate(0, 0.65)
    if incident:
        resolve_hours *= 1.6
    resolved = created + timedelta(hours=max(0.2, resolve_hours))

    escalate_chance = {"P1": 0.55, "P2": 0.22, "P3": 0.05, "P4": 0.01}[priority]
    escalated = 1 if rng.random() < escalate_chance else 0
    if escalated:
        agent_id = rng.choice(["A05", "A06", "A07", "A08", "A08"])
    elif rng.random() < 0.2:
        agent_id = rng.choice(["A05", "A06", "A07"])   # Tier 2 helps with the normal queue too
    else:
        agent_id = rng.choice(["A01", "A02", "A03", "A04"])

    # Some tickets are still being worked on at report time:
    # recent ones, and a few escalations that have been stuck for a while.
    age_days = (REPORT_TIME - created).total_seconds() / 86400
    still_open = resolved > REPORT_TIME
    if age_days < 5 and rng.random() < 0.30:
        still_open = True
    if escalated and age_days < 21 and rng.random() < 0.25:
        still_open = True

    status = "resolved"
    resolved_text = clock(resolved)
    first_response_text = clock(first_response)
    if still_open:
        status = rng.choice(["open", "open", "pending"])
        resolved_text = ""
        # Open tickets from the last 24 hours have not had a reply yet.
        if first_response > REPORT_TIME or age_days < 1:
            first_response_text = ""
            status = "open"

    # Satisfaction survey: about 60% of resolved tickets get a score.
    csat = ""
    if status == "resolved" and rng.random() < 0.6:
        score = 4.5
        if response_minutes > targets["first_response_minutes"]:
            score -= 1.0
        if resolve_hours > targets["resolution_hours"]:
            score -= 1.0
        if incident:
            score -= 0.7
        score += rng.gauss(0, 0.7)
        csat = int(min(5, max(1, round(score))))

    return {
        "ticket_id": f"T{ticket_number:04d}",
        "customer_id": customer["customer_id"],
        "agent_id": agent_id,
        "created_at": clock(created),
        "first_response_at": first_response_text,
        "resolved_at": resolved_text,
        "priority": priority,
        "category": category,
        "status": status,
        "escalated": escalated,
        "csat": csat,
        "subject": subject,
    }


def make_tickets(rng, customers):
    # Paying customers write in more often than free ones.
    contact_weight = {"Free": 1, "Pro": 3, "Enterprise": 5}
    weights = [contact_weight[c["plan"]] for c in customers]

    moments = []
    for day_number in range(NUMBER_OF_DAYS):
        day = FIRST_DAY + timedelta(days=day_number)
        is_weekend = day.weekday() >= 5
        for _ in range(rng.randint(2, 4) if is_weekend else rng.randint(7, 11)):
            hour = rng.choice(range(7, 20)) if not is_weekend else rng.choice(range(9, 18))
            moments.append((day + timedelta(hours=hour, minutes=rng.randint(0, 59),
                                            seconds=rng.randint(0, 59)), False))

    # The outage: a burst of login tickets during and just after the incident.
    for _ in range(38):
        minutes_in = rng.uniform(5, 260)
        moments.append((INCIDENT_START + timedelta(minutes=minutes_in), True))

    moments.sort()
    tickets = []
    for number, (created, incident) in enumerate(moments, start=1):
        customer = rng.choices(customers, weights=weights)[0]
        tickets.append(make_ticket(rng, number, created, customer, incident))
    return tickets


def make_product_events(rng, customers):
    """One row per thing a user did in the product (for the Day 3 funnel)."""
    # Chance of reaching each step, given the user reached the previous one.
    step_chance = {
        "Free":       {"project_created": 0.65, "teammate_invited": 0.22, "report_exported": 0.50},
        "Pro":        {"project_created": 0.82, "teammate_invited": 0.42, "report_exported": 0.70},
        "Enterprise": {"project_created": 0.92, "teammate_invited": 0.62, "report_exported": 0.85},
    }
    events = []
    user_number = 0
    for customer in customers:
        users = {"Free": rng.randint(1, 4), "Pro": rng.randint(3, 8),
                 "Enterprise": rng.randint(6, 14)}[customer["plan"]]
        for _ in range(users):
            user_number += 1
            user_id = f"U{user_number:04d}"
            moment = FIRST_DAY + timedelta(days=rng.randint(0, 41), hours=rng.randint(8, 18),
                                           minutes=rng.randint(0, 59))
            events.append((moment, user_id, customer["customer_id"], "signup"))
            reached_export = True
            for step in ["project_created", "teammate_invited", "report_exported"]:
                if rng.random() > step_chance[customer["plan"]][step]:
                    reached_export = False
                    break
                moment += timedelta(hours=rng.uniform(0.2, 72))
                events.append((moment, user_id, customer["customer_id"], step))
            # Engaged users keep exporting reports in later weeks.
            if reached_export:
                for _ in range(rng.randint(0, 6)):
                    moment += timedelta(days=rng.uniform(2, 9))
                    if moment < REPORT_TIME:
                        events.append((moment, user_id, customer["customer_id"], "report_exported"))

    events.sort()
    return [
        {"event_id": f"E{number:05d}", "user_id": user_id, "customer_id": customer_id,
         "event_name": name, "event_time": clock(moment)}
        for number, (moment, user_id, customer_id, name) in enumerate(events, start=1)
    ]


def make_log_lines(rng, customers):
    """Application log for 13 and 14 October: a normal day, then the outage."""
    normal = [
        ("INFO", "api-gateway", "GET /v1/reports 200"),
        ("INFO", "api-gateway", "GET /v1/projects 200"),
        ("INFO", "api-gateway", "POST /v1/reports/export 202"),
        ("INFO", "auth-service", "Login succeeded"),
        ("INFO", "auth-service", "Token refreshed"),
        ("INFO", "report-worker", "Report rendered"),
        ("INFO", "billing-service", "Invoice generated"),
        ("WARN", "report-worker", "Slow query on reports table"),
        ("WARN", "api-gateway", "Rate limit close to threshold"),
        ("ERROR", "report-worker", "Export failed: template not found"),
        ("ERROR", "billing-service", "Payment provider returned 502"),
    ]
    normal_weights = [20, 16, 8, 18, 12, 10, 4, 4, 3, 1, 1]
    outage = [
        ("ERROR", "auth-service", "Token validation failed: upstream timeout"),
        ("ERROR", "auth-service", "Database connection pool exhausted"),
        ("ERROR", "api-gateway", "POST /v1/login 503"),
        ("WARN", "auth-service", "Retrying identity provider request"),
    ]
    outage_weights = [40, 25, 25, 10]

    rows = []
    start = datetime(2026, 10, 13)
    for minute in range(2 * 24 * 60):
        moment = start + timedelta(minutes=minute)
        busy = 7 <= moment.hour < 20
        in_outage = INCIDENT_START <= moment < INCIDENT_END
        lines_this_minute = 0
        if rng.random() < (0.42 if busy else 0.08):
            lines_this_minute = 1
        for _ in range(lines_this_minute):
            level, service, message = rng.choices(normal, weights=normal_weights)[0]
            if in_outage and service == "auth-service":
                continue  # nobody can log in during the outage
            rows.append((moment + timedelta(seconds=rng.randint(0, 59)), level, service, message))
        if in_outage:
            for _ in range(rng.randint(1, 3)):
                level, service, message = rng.choices(outage, weights=outage_weights)[0]
                rows.append((moment + timedelta(seconds=rng.randint(0, 59)), level, service, message))

    rows.sort()
    lines = []
    for moment, level, service, message in rows:
        customer = rng.choice(customers)["customer_id"]
        request_id = f"{rng.getrandbits(32):08x}"
        if level == "ERROR":
            latency = rng.randint(5000, 30000)
        elif level == "WARN":
            latency = rng.randint(800, 5000)
        else:
            latency = rng.randint(20, 400)
        lines.append(
            f"{moment.strftime('%Y-%m-%dT%H:%M:%SZ')} {level:<5} {service} "
            f"request_id={request_id} customer_id={customer} latency_ms={latency} "
            f'msg="{message}"'
        )
    return lines


def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"  wrote {path.relative_to(DATA_DIR.parent)}  ({len(rows)} rows)")


def main():
    rng = random.Random(SEED)
    DATA_DIR.mkdir(exist_ok=True)
    print("Generating sample data ...")

    customers = make_customers(rng)
    write_csv(DATA_DIR / "customers.csv", customers)

    agents = [{"agent_id": a, "name": n, "team": t} for a, n, t in AGENTS]
    write_csv(DATA_DIR / "agents.csv", agents)

    write_csv(DATA_DIR / "tickets.csv", make_tickets(rng, customers))
    write_csv(DATA_DIR / "product_events.csv", make_product_events(rng, customers))

    policy = {
        "description": "Support SLA targets by priority. Clock time, not business hours.",
        "report_time": clock(REPORT_TIME),
        "targets": SLA_POLICY,
    }
    (DATA_DIR / "sla_policy.json").write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")
    print("  wrote data/sla_policy.json")

    lines = make_log_lines(rng, customers)
    (DATA_DIR / "app.log").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  wrote data/app.log  ({len(lines)} lines)")

    print("Done. (data/ticket_messages.json is hand-written and is not regenerated.)")


if __name__ == "__main__":
    main()
