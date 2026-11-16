"""A small API client class - the kind of code you will read in every SDK.

Used by 03_escalation_report.py and exercise.py:

    from helpdesk_client import connect_to_helpdesk
    client = connect_to_helpdesk()
    tickets = client.list_tickets(status="open,pending", priority="P1,P2")

Why a class? The base URL, the token and the open connection belong
together. The class keeps them in one object, so callers never repeat them.
"""

import os

import requests

from mock_helpdesk_api import DEMO_TOKEN, start_in_background


class HelpdeskClient:
    """Talks to the helpdesk API. One object = one configured connection."""

    # __init__ runs once, when you write HelpdeskClient(...). It stores the
    # settings on "self" (this object) so every method below can use them.
    def __init__(self, base_url, token, timeout_seconds=10):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()               # reuses one connection
        self.session.headers["Authorization"] = f"Bearer {token}"

    # A leading underscore means "internal helper, callers should not need it".
    def _request(self, method, path, **options):
        response = self.session.request(
            method, f"{self.base_url}{path}", timeout=self.timeout_seconds, **options
        )
        response.raise_for_status()                     # 4xx / 5xx -> raise an error
        return response.json()

    def get_ticket(self, ticket_id):
        return self._request("GET", f"/tickets/{ticket_id}")

    def list_tickets(self, **filters):
        """Return ALL matching tickets, following the pages for the caller."""
        tickets = []
        page = 1
        while page is not None:
            data = self._request("GET", "/tickets", params={**filters, "page": page, "per_page": 50})
            tickets.extend(data["tickets"])
            page = data["next_page"]                    # None on the last page
        return tickets

    def add_comment(self, ticket_id, body, internal=True):
        return self._request("POST", f"/tickets/{ticket_id}/comments",
                             json={"body": body, "internal": internal})


def connect_to_helpdesk():
    """Return a ready-to-use client.

    Default: start the offline mock API and connect to it.
    Real API: set HELPDESK_API_URL and HELPDESK_API_TOKEN before running.
    """
    base_url = os.environ.get("HELPDESK_API_URL")
    if base_url:
        token = os.environ.get("HELPDESK_API_TOKEN", "")
        print(f"[helpdesk] using the API at {base_url}")
    else:
        base_url = start_in_background()
        token = DEMO_TOKEN
        print(f"[helpdesk] using the offline mock API at {base_url}")
    return HelpdeskClient(base_url, token)
