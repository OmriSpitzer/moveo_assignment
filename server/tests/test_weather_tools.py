import unittest
from unittest.mock import patch

from agent.tools.weather_tools import URL_TIMEOUT, WeatherTools


class _Response:
    def __init__(self, url):
        self.url = url

    def raise_for_status(self):
        return None

    def json(self):
        return {
            "DisasterDeclarationsSummaries": [
                {"disasterNumber": 1, "incidentType": "Flood", "designatedArea": "Harris (County)"},
                {"disasterNumber": 2, "incidentType": "Flood", "designatedArea": "Harrison (County)"},
                {"disasterNumber": 3, "incidentType": "Fire", "designatedArea": "Maricopa (County)"},
                {"disasterNumber": 4, "incidentType": "Fire", "designatedArea": "Salt River Pima-Maricopa Indian Community"},
                {"disasterNumber": 5, "incidentType": "Fire", "designatedArea": "Maricopa Indian Reservation (Ak Chin)"},
            ]
        }


class WeatherToolTests(unittest.TestCase):
    def test_timeout_is_a_float(self):
        self.assertIsInstance(URL_TIMEOUT, float)
        self.assertGreater(URL_TIMEOUT, 0)

    def test_county_matches_the_area_name_exactly(self):
        seen = []

        def fake(url, params=None, timeout=None, headers=None):
            seen.append(type(timeout).__name__)
            return _Response(url)

        with patch("agent.tools.weather_tools.requests.get", fake):
            harris = WeatherTools._disaster_one({"state_code": "TX", "county": "Harris County"}, 2000)
            maricopa = WeatherTools._disaster_one({"state_code": "AZ", "county": "Maricopa"}, 2000)

        self.assertEqual(seen, ["float", "float"])
        self.assertEqual(harris.total_disasters, 1)
        self.assertEqual(maricopa.total_disasters, 1)

    def test_weather_history_description_is_one_sentence(self):
        description = WeatherTools.get_weather_history.description
        self.assertIn("high wind", description)
        self.assertIn("one call", description)
        self.assertNotIn("total_snowfall_cm", description)
        self.assertLess(len(description), 120)

    def test_other_weather_descriptions_are_one_sentence(self):
        descriptions = [
            tool.description for tool in WeatherTools.get_tools() if tool.name != "get_weather_history"
        ]
        self.assertEqual(len(descriptions), 3)
        self.assertTrue(all("one call" in description and len(description) < 140 for description in descriptions))
