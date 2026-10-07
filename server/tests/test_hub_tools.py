import inspect
import unittest

from agent.tools.hub_tools import HubTools
from agent.tools.location_tools import LocationTools
from agent.tools.weather_tools import WeatherTools


class HubToolTests(unittest.TestCase):
    def test_registered_tools_are_read_only(self):
        names = [
            tool.name
            for tool in HubTools.get_tools() + LocationTools.get_tools() + WeatherTools.get_tools()
        ]
        self.assertNotIn("set_hub", names)
        self.assertNotIn("decline_request", names)
        self.assertIn("list_hubs", names)
        self.assertIn("score_hubs", names)
        self.assertIn("get_location", names)
        self.assertIn("get_weather_history", names)
        self.assertIn("get_disaster_history", names)
        self.assertIn("get_active_alerts", names)
        self.assertIn("get_current_weather", names)

    def test_set_hub_does_not_geocode(self):
        source = inspect.getsource(HubTools.set_hub.func)
        self.assertNotIn("get_location.invoke", source)
        self.assertCountEqual(
            HubTools.set_hub.args.keys(),
            ["city", "county", "latitude", "longitude", "region", "state", "state_code"],
        )

    def test_hub_descriptions_are_one_sentence(self):
        descriptions = [
            HubTools.list_hubs.description,
            HubTools.score_hubs.description,
            HubTools.set_hub.description,
        ]
        self.assertEqual(len(descriptions), 3)
        self.assertTrue(all(len(description) < 160 for description in descriptions))
