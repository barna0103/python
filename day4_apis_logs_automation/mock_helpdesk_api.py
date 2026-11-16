"""A tiny pretend helpdesk API that runs on your own computer.

Real helpdesk tools (Zendesk, Jira Service Management, Freshdesk ...) need an
account and an API key. This stand-in behaves the same way - URLs, JSON,
status codes, a token, pages of results - but is free and works offline.

The other Day 4 scripts start it for you in the background. To watch it
handle requests, run it yourself in a second terminal:

    python day4_apis_logs_automation/mock_helpdesk_api.py

then open http://127.0.0.1:8765/api/v1/health in a browser.

Endpoints (all except /health need the header  Authorization: Bearer demo-token):
    GET  /api/v1/health
    GET  /api/v1/tickets?status=&priority=&escalated=&page=&per_page=
    GET  /api/v1/tickets/<ticket_id>
    POST /api/v1/tickets/<ticket_id>/comments      body: {"body": "...", "internal": true}
"""

import csv
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEMO_TOKEN = "demo-token"
DEFAULT_PORT = 8765


def read_csv(name):
    with open(DATA_DIR / f"{name}.csv", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def to_iso(text):
    """'2026-10-14 09:40:38' -> '2026-10-14T09:40:38Z' (how APIs usually send time)."""
    return text.replace(" ", "T") + "Z" if text else None


def load_tickets():
    """Build API-style tickets: nested JSON instead of flat CSV rows."""
    customers = {row["customer_id"]: row for row in read_csv("customers")}
    agents = {row["agent_id"]: row for row in read_csv("agents")}
    tickets = {}
    for row in read_csv("tickets"):
        customer = customers[row["customer_id"]]
        agent = agents[row["agent_id"]]
        tickets[row["ticket_id"]] = {
            "id": row["ticket_id"],
            "subject": row["subject"],
            "status": row["status"],
            "priority": row["priority"],
            "category": row["category"],
            "escalated": row["escalated"] == "1",
            "created_at": to_iso(row["created_at"]),
            "first_response_at": to_iso(row["first_response_at"]),
            "resolved_at": to_iso(row["resolved_at"]),
            "customer": {"id": customer["customer_id"], "name": customer["name"],
                         "plan": customer["plan"], "region": customer["region"]},
            "assignee": {"id": agent["agent_id"], "name": agent["name"], "team": agent["team"]},
            "comments": [],
        }
    return tickets


class HelpdeskHandler(BaseHTTPRequestHandler):
    tickets = {}          # filled in when the server starts
    quiet = True          # the background server does not print each request

    def log_message(self, format, *args):
        if not self.quiet:
            super().log_message(format, *args)

    def send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def is_authorised(self):
        if self.headers.get("Authorization") == f"Bearer {DEMO_TOKEN}":
            return True
        self.send_json(401, {"error": "Missing or invalid API token"})
        return False

    def do_GET(self):
        url = urlparse(self.path)
        parts = url.path.strip("/").split("/")          # ["api", "v1", "tickets", "T0001"]

        if parts == ["api", "v1", "health"]:
            return self.send_json(200, {"status": "ok", "tickets": len(self.tickets)})
        if not self.is_authorised():
            return None
        if parts == ["api", "v1", "tickets"]:
            return self.list_tickets(parse_qs(url.query))
        if len(parts) == 4 and parts[:3] == ["api", "v1", "tickets"]:
            ticket = self.tickets.get(parts[3])
            if ticket is None:
                return self.send_json(404, {"error": f"Ticket {parts[3]} not found"})
            return self.send_json(200, ticket)
        return self.send_json(404, {"error": f"No such endpoint: {url.path}"})

    def list_tickets(self, query):
        matches = list(self.tickets.values())
        for field in ["status", "priority"]:
            if field in query:
                wanted = query[field][0].split(",")          # ?priority=P1,P2
                matches = [t for t in matches if t[field] in wanted]
        if "escalated" in query:
            wanted = query["escalated"][0].lower() == "true"
            matches = [t for t in matches if t["escalated"] == wanted]

        page = int(query.get("page", ["1"])[0])
        per_page = min(int(query.get("per_page", ["10"])[0]), 50)
        start = (page - 1) * per_page
        chunk = matches[start:start + per_page]
        has_more = start + per_page < len(matches)
        return self.send_json(200, {
            "tickets": chunk,
            "page": page,
            "per_page": per_page,
            "total": len(matches),
            "next_page": page + 1 if has_more else None,
        })

    def do_POST(self):
        parts = urlparse(self.path).path.strip("/").split("/")
        if not self.is_authorised():
            return None
        if len(parts) == 5 and parts[:3] == ["api", "v1", "tickets"] and parts[4] == "comments":
            ticket = self.tickets.get(parts[3])
            if ticket is None:
                return self.send_json(404, {"error": f"Ticket {parts[3]} not found"})
            length = int(self.headers.get("Content-Length", 0))
            try:
                payload = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                return self.send_json(400, {"error": "Body must be JSON"})
            if not payload.get("body"):
                return self.send_json(400, {"error": "Field 'body' is required"})
            comment = {
                "id": len(ticket["comments"]) + 1,
                "body": payload["body"],
                "internal": bool(payload.get("internal", True)),
            }
            ticket["comments"].append(comment)
            return self.send_json(201, comment)
        return self.send_json(404, {"error": "No such endpoint"})


def make_server(port, quiet):
    HelpdeskHandler.tickets = load_tickets()
    HelpdeskHandler.quiet = quiet
    return ThreadingHTTPServer(("127.0.0.1", port), HelpdeskHandler)


def start_in_background():
    """Start the API on a free port and return its base URL.

    The server runs in a background thread and stops when your script ends.
    """
    server = make_server(port=0, quiet=True)             # port 0 = "pick any free port"
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{server.server_port}/api/v1"


if __name__ == "__main__":
    server = make_server(DEFAULT_PORT, quiet=False)
    print(f"Mock helpdesk API running at http://127.0.0.1:{DEFAULT_PORT}/api/v1")
    print(f"Token: {DEMO_TOKEN}   |   Stop with Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
