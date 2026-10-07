import unittest

from eval.cases import CASES
from eval.check import grade_turn


class GradeTests(unittest.TestCase):
    def test_grade_turn_checks_tools_and_answer_text(self):
        passed = grade_turn(
            {
                "tools": ["get_weather_history"],
                "forbid": ["score_hubs"],
                "args": {"get_weather_history": ["2025"]},
                "pattern": r"\d+(\.\d+)?\s*(%|percent)",
                "lacks": ["sources:"],
            },
            [
                {"type": "tool_call", "name": "get_weather_history", "args": {"start_date": "2025-01-01"}},
                {"type": "answer", "answer": {"answer": "12.1% of days had snow."}},
            ],
        )
        failed = grade_turn(
            {"no_tools": True, "question": True},
            [
                {"type": "tool_call", "name": "list_hubs"},
                {"type": "answer", "answer": {"answer": "Denver had snow."}},
            ],
        )
        self.assertEqual(passed, [])
        self.assertEqual(failed, ["called list_hubs", "answer is not a question"])
        self.assertEqual(len(CASES), 6)
        self.assertEqual(len({case["name"] for case in CASES}), len(CASES))

    def test_not_a_hub_accepts_either_wording(self):
        turn = next(case for case in CASES if case["name"] == "not a hub")["turns"][0]
        events = [
            {"type": "tool_call", "name": "list_hubs"},
            {"type": "answer", "answer": {"answer": "Paris is not one of our company hubs."}},
        ]
        self.assertEqual(grade_turn(turn, events), [])
