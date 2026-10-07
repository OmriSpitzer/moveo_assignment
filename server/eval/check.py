import re

"""
    Grade one streamed agent turn against an eval turn.

    grade_turn returns a list of failure reasons. An empty list means the turn passed.
"""

# Grade one turn from the events stream() yielded
def grade_turn(turn: dict, events: list[dict]) -> list[str]:
    failures = []
    calls = [event for event in events if event.get("type") == "tool_call"]
    names = [event.get("name") for event in calls]
    answer_event = next((event for event in reversed(events) if event.get("type") == "answer"), None)
    error_event = next((event for event in events if event.get("type") == "error"), None)

    if error_event is not None or answer_event is None:
        failures.append(error_event["message"] if error_event else "no answer")
        return failures

    answer = str(answer_event["answer"]["answer"])
    folded = answer.casefold()

    if turn.get("no_tools") and names:
        failures.append("called " + ", ".join(str(name) for name in names))

    for name in turn.get("tools") or []:
        if name not in names:
            failures.append(f"missing {name}")

    for name in turn.get("forbid") or []:
        if name in names:
            failures.append(f"called {name}")

    for name, needles in (turn.get("args") or {}).items():
        matched = [event for event in calls if event.get("name") == name]
        blob = " ".join(str(event.get("args")) for event in matched).casefold()
        for needle in needles:
            if needle.casefold() not in blob:
                failures.append(f"{name} args missing {needle}")

    for text in turn.get("has") or []:
        if text.casefold() not in folded:
            failures.append(f"answer missing {text}")

    options = turn.get("has_any") or []
    if options and not any(text.casefold() in folded for text in options):
        failures.append("answer missing one of " + ", ".join(options))

    for text in turn.get("lacks") or []:
        if text.casefold() in folded:
            failures.append(f"answer has {text}")

    pattern = turn.get("pattern")
    if pattern and re.search(pattern, answer, re.IGNORECASE) is None:
        failures.append(f"answer missed pattern {pattern}")

    if turn.get("question") and not answer.strip().endswith("?"):
        failures.append("answer is not a question")

    return failures
