"""Day 4, example 1: talk to a web API, one step at a time.

Run it:   python day4_apis_logs_automation/01_call_an_api.py
          python day4_apis_logs_automation/01_call_an_api.py --live   (also calls a real public API)

Scenario: the helpdesk tool has an API. Instead of exporting a CSV by hand
every morning, a script can ask for exactly the tickets it needs.

An API call is: a URL + a method (GET = read, POST = create) + optional
headers (who you are) and parameters (what you want). The answer is a
status code (did it work?) and usually JSON (the data).
"""

import sys

import requests

from mock_helpdesk_api import DEMO_TOKEN, start_in_background

BASE_URL = start_in_background()                 # e.g. http://127.0.0.1:54321/api/v1
HEADERS = {"Authorization": f"Bearer {DEMO_TOKEN}"}
print(f"Mock helpdesk API is running at {BASE_URL}\n")

# --- 1. GET one ticket ---------------------------------------------------------------
response = requests.get(f"{BASE_URL}/tickets/T0296", headers=HEADERS, timeout=10)
print("1. GET /tickets/T0296")
print("   status code:", response.status_code, "(200 = OK)")
print("   content type:", response.headers["Content-Type"])

ticket = response.json()                         # JSON text -> Python dict
print("   keys:", ", ".join(ticket.keys()))
print("   subject:", ticket["subject"])
# JSON is often nested: a dict inside a dict. Chain the keys to drill down.
print("   customer:", ticket["customer"]["name"], f"({ticket['customer']['plan']})")
print("   assignee:", ticket["assignee"]["name"], "-", ticket["assignee"]["team"])

# --- 2. Ask for a filtered list with query parameters --------------------------------
# requests turns the dict into ?status=open&priority=P1 at the end of the URL.
response = requests.get(f"{BASE_URL}/tickets", headers=HEADERS, timeout=10,
                        params={"status": "open", "priority": "P1"})
data = response.json()
print("\n2. GET", response.url.replace(BASE_URL, ""))
print(f"   {data['total']} open P1 tickets. The first three:")
for item in data["tickets"][:3]:
    print(f"   - {item['id']}  {item['created_at']}  {item['customer']['name']}: {item['subject']}")

# --- 3. Things go wrong: read the status code ----------------------------------------
missing = requests.get(f"{BASE_URL}/tickets/T9999", headers=HEADERS, timeout=10)
print("\n3. GET /tickets/T9999 ->", missing.status_code, missing.json())

no_token = requests.get(f"{BASE_URL}/tickets/T0296", timeout=10)
print("   Same call without a token ->", no_token.status_code, no_token.json())

# raise_for_status() turns a bad status code into a Python error you can catch.
try:
    missing.raise_for_status()
except requests.HTTPError as error:
    print("   raise_for_status() said:", str(error).replace(BASE_URL, ""))

# --- 4. Pagination: big lists arrive one page at a time ------------------------------
print("\n4. All escalated tickets, 10 per page")
escalated = []
page = 1
while page is not None:
    data = requests.get(f"{BASE_URL}/tickets", headers=HEADERS, timeout=10,
                        params={"escalated": "true", "page": page, "per_page": 10}).json()
    escalated.extend(data["tickets"])
    print(f"   page {data['page']}: got {len(data['tickets'])} tickets, next page: {data['next_page']}")
    page = data["next_page"]
print(f"   collected {len(escalated)} of {data['total']} escalated tickets")

# --- 5. POST: send data to create something ------------------------------------------
note = {"body": "Customer called again. Raising with the on-call engineer.", "internal": True}
created = requests.post(f"{BASE_URL}/tickets/T0296/comments", headers=HEADERS, json=note, timeout=10)
print("\n5. POST /tickets/T0296/comments ->", created.status_code, "(201 = created)")
print("   server replied:", created.json())

after = requests.get(f"{BASE_URL}/tickets/T0296", headers=HEADERS, timeout=10).json()
print("   the ticket now has", len(after["comments"]), "comment")

# --- 6. Optional: the same pattern against a real API on the internet ----------------
if "--live" in sys.argv:
    print("\n6. A real public API (GitHub). Same pattern, different URL.")
    try:
        live = requests.get("https://api.github.com/repos/pandas-dev/pandas", timeout=10)
        live.raise_for_status()
        repo = live.json()
        print(f"   {repo['full_name']}: {repo['stargazers_count']} stars, "
              f"{repo['open_issues_count']} open issues, license {repo['license']['spdx_id']}")
    except requests.RequestException as error:
        print("   Could not reach the internet (that is fine, the rest works offline):", error)
else:
    print("\n6. Skipped the real internet call. Add --live to try it.")
