"""Day 5, example 1: use an LLM to triage tickets - and measure how good it is.

Run it:   python day5_llm_agents/01_classify_tickets.py

Scenario: 12 new tickets arrived overnight as free text. Someone has to
read each one and set a category and a priority. Can a model do the first
pass? Do not guess - compare it with what a human chose.

The pattern (the same for almost every LLM feature):
    prompt with clear rules  ->  model  ->  text  ->  parse + validate  ->  measure
"""

import json
from pathlib import Path

from llm import get_llm

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CATEGORIES = ["Login", "Billing", "Performance", "Bug", "How-to", "Integration"]
PRIORITIES = ["P1", "P2", "P3", "P4"]

# The system prompt is the standing instruction: role, rules, output format.
SYSTEM_PROMPT = f"""You are a support triage assistant for Northbeam, a SaaS reporting tool.
Classify the ticket you are given.

Categories: {", ".join(CATEGORIES)}
Priorities:
- P1: service down or many users blocked right now
- P2: serious impact or a deadline within days, but a workaround or partial service exists
- P3: normal problem, no urgency
- P4: question or minor request

Answer with JSON only, in exactly this shape:
{{"category": "...", "priority": "...", "reason": "one short sentence"}}"""


def build_prompt(message):
    # Tags keep the customer's text clearly separate from our instructions.
    return f"<ticket>\nSubject: {message['subject']}\n\n{message['body']}\n</ticket>"


def parse_answer(text):
    """Turn the model's text into a checked dict. Returns None if it is unusable.

    Never trust model output blindly: it is text that usually - not always -
    follows your format.
    """
    start, end = text.find("{"), text.rfind("}")          # ignore code fences or chatter
    if start == -1 or end == -1:
        return None
    try:
        answer = json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None
    if answer.get("category") not in CATEGORIES or answer.get("priority") not in PRIORITIES:
        return None
    return answer


llm = get_llm()
messages = json.loads((DATA_DIR / "ticket_messages.json").read_text(encoding="utf-8"))

results = []
print(f"\nClassifying {len(messages)} tickets ...\n")
print(f"{'id':<5}{'model says':<22}{'human says':<22}{'match':<7}reason")
for message in messages:
    answer = parse_answer(llm.ask(SYSTEM_PROMPT, build_prompt(message)))
    if answer is None:
        answer = {"category": "INVALID", "priority": "INVALID", "reason": "could not parse the answer"}

    category_ok = answer["category"] == message["human_category"]
    priority_ok = answer["priority"] == message["human_priority"]
    results.append({"message": message, "answer": answer,
                    "category_ok": category_ok, "priority_ok": priority_ok})

    model_label = f"{answer['category']} / {answer['priority']}"
    human_label = f"{message['human_category']} / {message['human_priority']}"
    match = "yes" if category_ok and priority_ok else "NO"
    print(f"{message['message_id']:<5}{model_label:<22}{human_label:<22}{match:<7}{answer['reason']}")

# --- Measure: this small table of labelled examples is called an "eval" ---------------
total = len(results)
category_hits = sum(result["category_ok"] for result in results)
priority_hits = sum(result["priority_ok"] for result in results)
print(f"\nCategory accuracy: {category_hits}/{total} ({category_hits / total:.0%})")
print(f"Priority accuracy: {priority_hits}/{total} ({priority_hits / total:.0%})")

# The dangerous mistake is an urgent ticket that the model rated as not urgent.
missed_urgent = [result for result in results
                 if result["message"]["human_priority"] in ("P1", "P2")
                 and result["answer"]["priority"] not in ("P1", "P2")]
print(f"Urgent tickets (P1/P2) the model rated lower: {len(missed_urgent)}")
for result in missed_urgent:
    print(f"  {result['message']['message_id']}: {result['message']['subject']}")

print("\nDecide with numbers: is this good enough to pre-fill fields for a human to confirm?")
print("Good enough to act with no human at all? Those are different bars.")
