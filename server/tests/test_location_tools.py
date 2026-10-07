import unittest
from unittest.mock import patch

from agent.schema.tool_results import Location, ToolError
from agent.tools.location_tools import LocationTools


class _Response:
    def __init__(self, results):
        self._results = results

    def raise_for_status(self):
        return None

    def json(self):
        return {"results": self._results}


def _place(name, admin1, latitude):
    return {
        "name": name,
        "latitude": latitude,
        "longitude": -100.0,
        "admin1": admin1,
        "admin2": name,
    }


class LocationToolTests(unittest.TestCase):
    def test_one_call_keeps_order_and_reports_a_miss(self):
        found = {
            "Denver": [_place("Denver", "Colorado", 39.74)],
            "Miami": [_place("Miami", "Florida", 25.76)],
        }

        def fake(url, params=None, timeout=None, headers=None):
            self.assertIsInstance(timeout, float)
            return _Response(found.get(params["name"], []))

        with patch("agent.tools.location_tools.requests.get", fake):
            results = LocationTools.get_location.invoke({
                "cities": ["Denver", "Miami", "NotARealCity"],
                "state_codes": ["CO", "FL", "ZZ"],
            })

        self.assertIsInstance(results[0], Location)
        self.assertIsInstance(results[1], Location)
        self.assertIsInstance(results[2], ToolError)
        self.assertEqual(results[0].state_code, "CO")
        self.assertEqual(results[1].state_code, "FL")
        self.assertEqual(round(results[0].latitude, 2), 39.74)
