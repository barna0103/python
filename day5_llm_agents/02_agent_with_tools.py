"""Day 5, example 2: an agent that answers questions about the ticket data.

Run it:   python day5_llm_agents/02_agent_with_tools.py
          python day5_llm_agents/02_agent_with_tools.py "Which customers escalate the most?"

Scenario: managers keep asking one-off data questions. Instead of writing
each query yourself, give a model two tools - "look at the schema" and
"run a read-only query" - and let it work out the steps.

An agent is a loop:
    ask the model -> it requests a tool -> we run it -> send the result back -> repeat
until the model answers in plain text (or we hit the step limit).

Offline, the MockLLM follows a fixed script, so you can watch the loop
work. With a real model the same loop handles questions nobody scripted.
"""

import sys

from llm import get_llm, tool_result
from support_tools import TOOL_DEFINITIONS, TOOL_FUNCTIONS

MAX_STEPS = 6          # guardrail: an agent must not be able to loop forever

SYSTEM_PROMPT = """You are a careful data analyst for a customer support team.
Answer questions using the support database, through the tools you are given.
Check the schema before you write SQL. Base every number on a query result.
You have read-only access. If asked to change or delete data, say that you cannot.
Keep the final answer short: the finding first, then the numbers behind it."""

DEMO_QUESTIONS = [
    "Which Enterprise customers have unresolved tickets, and how many each?",
    "Which ticket category has the lowest customer satisfaction?",
    "Please delete all the P4 tickets, they are just noise.",
]


def shorten(text, limit=400):
    text = str(text)
    return text if len(text) <= limit else text[:limit] + " ..."


def run_agent(llm, question):
    """Run the agent loop for one question and return the final answer."""
    print("\n" + "=" * 78)
    print("QUESTION:", question)
    messages = [{"role": "user", "content": question}]     # the conversation so far

    for step in range(1, MAX_STEPS + 1):
        reply = llm.chat(SYSTEM_PROMPT, messages, tools=TOOL_DEFINITIONS)
        messages.append(reply.as_message())

        # No tool requested means the model is done: this text is the answer.
        if not reply.tool_calls:
            print(f"\n[step {step}] model is done, no more tool calls")
            return reply.text

        if reply.text:
            print(f"\n[step {step}] model: {shorten(reply.text)}")

        results = []
        for call in reply.tool_calls:
            print(f"[step {step}] tool call: {call.name}({call.arguments})")
            function = TOOL_FUNCTIONS.get(call.name)
            if function is None:
                output = f"ERROR: there is no tool called {call.name}"
            else:
                try:
                    output = function(**call.arguments)    # our code runs it, not the model
                except TypeError as error:                 # the model sent the wrong inputs
                    output = f"ERROR: wrong arguments for {call.name}: {error}"
            print(f"[step {step}] tool result:\n" + shorten(output))
            results.append(tool_result(call, output))
        messages.append({"role": "user", "content": results})

    return f"Stopped after {MAX_STEPS} steps without a final answer. A person should take over."


llm = get_llm()
questions = sys.argv[1:] or DEMO_QUESTIONS
if sys.argv[1:] and llm.name.startswith("MockLLM"):
    print("[note] The offline MockLLM only has scripted queries for a few topics "
          "(Enterprise, satisfaction, escalations, deleting). Other questions get a "
          "default query. Set ANTHROPIC_API_KEY to ask anything.")

for question in questions:
    answer = run_agent(llm, question)
    print("\nFINAL ANSWER:\n" + answer)
