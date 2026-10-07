import sys
import uuid
from langchain_core.messages import HumanMessage
from eval.cases import CASES
from eval.check import grade_turn

"""
    Run the evaluation set against the Ollama agent.

    Usage, from server/:
        python -m eval.run
        python -m eval.run snow days
"""

# Stream one user turn and return the events
def _events(agent, thread_id: str, content: str) -> list[dict]:
    return list(agent.stream([HumanMessage(content=content)], thread_id))

# Run every selected case. Return the number that failed.
def run_cases(agent, cases: list[dict]) -> int:
    failed = 0
    for case in cases:
        thread_id = str(uuid.uuid4())
        reasons = []
        for index, turn in enumerate(case["turns"], start=1):
            events = _events(agent, thread_id, turn["content"])
            turn_reasons = grade_turn(turn, events)
            if turn_reasons:
                label = f"turn {index}" if len(case["turns"]) > 1 else "turn"
                tools = [event.get("name") for event in events if event.get("type") == "tool_call"]
                answer = next((event for event in reversed(events) if event.get("type") == "answer"), None)
                text = "" if answer is None else str(answer["answer"]["answer"])
                reasons.append(f"{label}: " + "; ".join(turn_reasons))
                reasons.append(f"tools: {tools}")
                reasons.append(f"answer: {text[:500]}")
        if reasons:
            failed += 1
            print(f"fail  {case['name']}")
            for line in reasons:
                print(f"  {line}")
        else:
            print(f"pass  {case['name']}")
    print(f"{len(cases) - failed}/{len(cases)} passed")
    return failed

def main() -> None:
    from agent.providers.ollama_agent import OllamaAgent

    query = " ".join(sys.argv[1:]).casefold()
    selected = [case for case in CASES if not query or query in case["name"].casefold()]
    if not selected:
        print(f"no case named {query}")
        sys.exit(1)
    failed = run_cases(OllamaAgent(), selected)
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
