"""One door to "the LLM" for all Day 5 scripts.

    from llm import get_llm
    llm = get_llm()
    print(llm.ask("You are a helpful analyst.", "Say hello"))

get_llm() hands back one of two objects that behave the same way:

  * MockLLM   - default. A rule-based stand-in. No key, no cost, no internet.
                It is NOT intelligent; it exists so you can run every example
                and see how the plumbing works.
  * ClaudeLLM - used when the ANTHROPIC_API_KEY environment variable is set.
                Calls a real model through the official `anthropic` package.

Because both have the same methods, the scripts never need to know which
one they got. That "same shape, different insides" trick is the main reason
classes exist, and you will see it in every modern Python library.

Switching to the real model:
    macOS/Linux:  export ANTHROPIC_API_KEY="sk-ant-..."
    Windows:      $env:ANTHROPIC_API_KEY="sk-ant-..."
Optional:  ANTHROPIC_MODEL=<model id>  to pick a different model
           LLM_MODE=mock               to force the offline stand-in
"""

import json
import os
import re
from dataclasses import dataclass, field

DEFAULT_MODEL = "claude-sonnet-5-5"


@dataclass
class ToolCall:
    """The model asking us to run one of our functions."""
    id: str
    name: str
    arguments: dict


@dataclass
class Reply:
    """What comes back from one call to the model."""
    text: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw_content: list | None = None     # the provider's own version of this reply

    def as_message(self):
        """This reply in the shape the conversation history needs."""
        if self.raw_content is not None:
            return {"role": "assistant", "content": self.raw_content}
        blocks = [{"type": "text", "text": self.text}] if self.text else []
        for call in self.tool_calls:
            blocks.append({"type": "tool_use", "id": call.id, "name": call.name,
                           "input": call.arguments})
        return {"role": "assistant", "content": blocks}


def tool_result(call, output):
    """Wrap what a tool returned so it can be sent back to the model."""
    return {"type": "tool_result", "tool_use_id": call.id, "content": str(output)}


class LLM:
    """The shape every LLM in this course has. The two classes below fill it in."""

    name = "base"

    def chat(self, system, messages, tools=None):
        """Send the conversation so far, get a Reply back."""
        raise NotImplementedError

    def ask(self, system, prompt):
        """Shortcut for a single question with a text answer."""
        return self.chat(system, [{"role": "user", "content": prompt}]).text


# ---------------------------------------------------------------------------------------
# The real thing
# ---------------------------------------------------------------------------------------
class ClaudeLLM(LLM):                       # "(LLM)" = this is a kind of LLM
    def __init__(self, model=None):
        import anthropic                    # imported here so the mock works without it

        self.client = anthropic.Anthropic()                 # reads ANTHROPIC_API_KEY itself
        self.api_error = anthropic.APIError                 # what the client raises on failure
        self.model = model or os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)
        self.name = f"Claude ({self.model})"

    def chat(self, system, messages, tools=None):
        options = {"tools": tools} if tools else {}
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system,
                messages=messages,
                **options,
            )
        except self.api_error as error:
            raise SystemExit(
                f"The call to the real model failed: {error}\n"
                "Check ANTHROPIC_API_KEY and ANTHROPIC_MODEL, or run offline with LLM_MODE=mock."
            ) from None
        # The answer is a list of blocks: text, and/or requests to use a tool.
        text = "".join(block.text for block in response.content if block.type == "text")
        calls = [ToolCall(block.id, block.name, block.input)
                 for block in response.content if block.type == "tool_use"]
        return Reply(text, calls, raw_content=response.content)


# ---------------------------------------------------------------------------------------
# The offline stand-in
# ---------------------------------------------------------------------------------------
class MockLLM(LLM):
    """Pretends to be a model using simple rules. Good for learning the plumbing.

    It recognises the three jobs this course gives it:
      1. a ticket inside <ticket> tags     -> classify it with keyword rules
      2. numbers inside <metrics> tags     -> fill in a summary template
      3. a question plus tools             -> follow a fixed script of tool calls
    """

    name = "MockLLM (offline, rule-based)"

    def chat(self, system, messages, tools=None):
        if tools:
            return self._agent_step(messages)
        prompt = messages[-1]["content"]
        if "<ticket>" in prompt:
            return Reply(self._classify(prompt))
        if "<metrics>" in prompt:
            return Reply(self._summarise(prompt))
        return Reply("[mock] I am an offline stand-in and only know this course's examples. "
                     "Set ANTHROPIC_API_KEY to talk to a real model.")

    # --- job 1: classification by keyword ----------------------------------------------
    def _classify(self, prompt):
        ticket = prompt.split("<ticket>")[1].split("</ticket>")[0].lower()

        category_rules = [                  # first match wins - crude on purpose
            ("Login", ["log in", "sign in", "password", "two-factor", "locked out"]),
            ("Billing", ["charged", "invoice", "refund", "card", "payment"]),
            ("Integration", ["salesforce", "slack", "api", "webhook", "sync"]),
            ("Performance", ["slow", "timing out", "takes over", "to load"]),
            ("Bug", ["crash", "does not match", "wrong", "error"]),
            ("How-to", ["how do i", "is there a way", "where can i"]),
        ]
        category = "Bug"
        matched_word = "no keyword matched"
        for name, words in category_rules:
            hits = [word for word in words if word in ticket]
            if hits:
                category, matched_word = name, f"mentions '{hits[0]}'"
                break

        if any(word in ticket for word in ["urgent", "down"]):
            priority = "P1"
        elif any(word in ticket for word in ["tomorrow", "deadline", "asap"]):
            priority = "P2"
        elif any(word in ticket for word in ["how do i", "is there a way"]):
            priority = "P4"
        else:
            priority = "P3"

        answer = json.dumps({"category": category, "priority": priority, "reason": matched_word})
        # Real models sometimes wrap JSON in a code fence. Do the same now and
        # then, so the calling code has to cope with it.
        if len(ticket) % 3 == 0:
            answer = f"```json\n{answer}\n```"
        return answer

    # --- job 2: summary from a template ------------------------------------------------
    def _summarise(self, prompt):
        m = json.loads(prompt.split("<metrics>")[1].split("</metrics>")[0])
        this, prev = m["this_week"], m["previous_week"]
        sla_word = "above" if this["sla_met_pct"] >= m["sla_goal_pct"] else "below"
        lines = [
            f"- Volume: {this['tickets']} tickets in the week of {m['week_start']}, "
            f"compared with {prev['tickets']} the week before.",
            f"- SLA: {this['sla_met_pct']}% of first replies were in time, {sla_word} the "
            f"{m['sla_goal_pct']}% goal (previous week: {prev['sla_met_pct']}%).",
            f"- Satisfaction: average CSAT {this['avg_csat']} (previous week: {prev['avg_csat']}). "
            f"Busiest category: {m['top_categories'][0]['category']} "
            f"with {m['top_categories'][0]['tickets']} tickets.",
        ]
        urgent = m["unresolved_urgent"]
        if urgent:
            oldest = urgent[0]
            lines.append(
                f"- Watch: {m['unresolved_urgent_count']} P1/P2 tickets are still unresolved. The oldest is "
                f"{oldest['ticket_id']} for {oldest['customer']} ({oldest['age_days']} days).")
        else:
            lines.append("- Watch: no unresolved P1/P2 tickets.")
        return "\n".join(lines)

    # --- job 3: a scripted "agent" -----------------------------------------------------
    def _agent_step(self, messages):
        question = messages[0]["content"].lower()
        results = [block["content"] for message in messages
                   if isinstance(message["content"], list)
                   for block in message["content"]
                   if isinstance(block, dict) and block.get("type") == "tool_result"]
        step = len(results)

        if step == 0:
            return Reply("First I need to know which tables and columns exist.",
                         [ToolCall("call_1", "get_schema", {})])
        if step == 1:
            return Reply("Now I can write a query for this question.",
                         [ToolCall("call_2", "run_sql", {"query": self._pick_sql(question)})])

        last = results[-1]
        if last.startswith("REFUSED") or last.startswith("ERROR"):
            return Reply("I could not do that. The tool answered: " + last +
                         "\nI only have read access to this data, so a person has to make that change.")
        return Reply("Here is what the data shows:\n" + last)

    def _pick_sql(self, question):
        if re.search(r"\b(delete|remove|update|drop)\b", question):
            return "DELETE FROM tickets WHERE priority = 'P4'"
        if "enterprise" in question:
            return ("SELECT c.name, COUNT(*) AS unresolved_tickets "
                    "FROM tickets AS t JOIN customers AS c ON c.customer_id = t.customer_id "
                    "WHERE c.plan = 'Enterprise' AND t.status != 'resolved' "
                    "GROUP BY c.name ORDER BY unresolved_tickets DESC")
        if "satisf" in question or "csat" in question:
            return ("SELECT category, ROUND(AVG(csat), 2) AS avg_csat, COUNT(csat) AS rated "
                    "FROM tickets GROUP BY category ORDER BY avg_csat")
        if "escalat" in question:
            return ("SELECT c.name, c.plan, COUNT(*) AS escalated_tickets "
                    "FROM tickets AS t JOIN customers AS c ON c.customer_id = t.customer_id "
                    "WHERE t.escalated = 1 GROUP BY c.name, c.plan "
                    "ORDER BY escalated_tickets DESC LIMIT 5")
        return "SELECT status, COUNT(*) AS tickets FROM tickets GROUP BY status ORDER BY tickets DESC"


def get_llm():
    """Return the real model if a key is set, otherwise the offline stand-in."""
    has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    forced_mock = os.environ.get("LLM_MODE", "").lower() == "mock"

    if has_key and not forced_mock:
        try:
            llm = ClaudeLLM()
        except ImportError:
            raise SystemExit("ANTHROPIC_API_KEY is set but the 'anthropic' package is missing. "
                             "Run: pip install -r requirements.txt") from None
        print(f"[llm] Using the real model: {llm.name}")
        return llm

    reason = "LLM_MODE=mock" if forced_mock else "no ANTHROPIC_API_KEY set"
    print(f"[llm] Using {MockLLM.name} because {reason}.")
    return MockLLM()
