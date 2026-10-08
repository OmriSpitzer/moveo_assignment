import inspect
import unittest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

from agent.schema.tool_results import ActiveAlerts, Alert, DisasterHistory, WeatherHistory
from agent.tools.hub_tools import HubTools, drain_score_alerts
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
            ["city", "county", "excluded", "factors", "latitude", "longitude", "region", "score", "scored_at", "state", "state_code"],
        )

    def test_set_hub_writes_score_and_timestamp(self):
        saved = {}

        def set_fields(query, fields, upsert=False):
            saved["query"] = query
            saved["fields"] = fields

        when = datetime(2026, 10, 6, tzinfo=timezone.utc)
        with patch("agent.tools.hub_tools.DbTools.find_one", return_value={"city": "Denver", "state_code": "CO", "region": "West"}), \
             patch("agent.tools.hub_tools.DbTools.set_fields", set_fields):
            hub = HubTools.set_hub.func(
                city="Denver", state_code="CO", region="West", latitude=39.7, longitude=-104.9, score=12.5, scored_at=when,
            )
        self.assertEqual(hub.city, "Denver")
        self.assertEqual(saved["fields"], {"score": 12.5, "scored_at": when})
        self.assertNotIn("weather", saved["fields"])

    def test_stale_score_updates_through_set_hub_and_alerts(self):
        drain_score_alerts()
        doc = {
            "city": "Denver", "city_key": "denver", "state_code": "CO", "region": "West",
            "score": 0, "scored_at": datetime.now(timezone.utc) - timedelta(days=2),
            "location": {"latitude": 39.7, "longitude": -104.9, "state": "Colorado", "county": "Denver"},
        }
        saved = {}

        def find_one(query):
            return doc if query.get("city_key") == "denver" else None

        def set_fields(query, fields, upsert=False):
            saved.update(fields)

        weather = WeatherHistory(
            source="t", latitude=0, longitude=0, start_date="2025-01-01", end_date="2025-12-31",
            days=365, snow_days=0, freezing_days=0, heavy_rain_days=0, high_wind_days=0,
            snow_days_pct=0, freezing_days_pct=0, heavy_rain_days_pct=10, high_wind_days_pct=0,
            total_snowfall_cm=0, heavy_rain_threshold_mm=25, high_wind_threshold_kmh=60, freezing_threshold_c=0,
        )
        disasters = DisasterHistory(
            source="t", state="CO", county="Denver", since_year=date.today().year,
            total_disasters=4, by_incident_type={"Hurricane": 4},
        )
        alerts = ActiveAlerts(
            source="t", latitude=0, longitude=0, active_alert_count=1,
            alerts=[Alert(event="Hurricane Warning", severity="Extreme", headline=None, expires=None)],
        )

        class Call:
            def __init__(self, value):
                self.value = value

            def invoke(self, args):
                return [self.value]

        with patch("agent.tools.hub_tools.DbTools.find_one", find_one), \
             patch("agent.tools.hub_tools.DbTools.set_fields", set_fields), \
             patch("agent.tools.hub_tools.WeatherTools.get_weather_history", Call(weather)), \
             patch("agent.tools.hub_tools.WeatherTools.get_disaster_history", Call(disasters)), \
             patch("agent.tools.hub_tools.WeatherTools.get_active_alerts", Call(alerts)):
            scored = HubTools.score_hubs.func(["Denver"])

        self.assertEqual(scored[0].score, 65.0)
        self.assertTrue(scored[0].refreshed)
        self.assertEqual(saved["score"], 65.0)
        self.assertTrue(saved["factors"])
        self.assertIsInstance(saved["scored_at"], datetime)
        self.assertEqual(drain_score_alerts(), [{
            "type": "score_alert", "city": "Denver", "previous": 0.0, "score": 65.0,
        }])

    def test_fresh_score_is_kept(self):
        drain_score_alerts()
        doc = {
            "city": "Denver", "city_key": "denver", "state_code": "CO", "region": "West",
            "score": 0, "scored_at": datetime.now(timezone.utc),
            "factors": [{"name": "Snow days", "points": 0.0, "weight": 15.0, "detail": "0% of days"}],
            "location": {"latitude": 39.7, "longitude": -104.9},
        }

        def fail_set(query, fields, upsert=False):
            raise AssertionError("fresh score was written")

        with patch("agent.tools.hub_tools.DbTools.find_one", return_value=doc), \
             patch("agent.tools.hub_tools.DbTools.set_fields", fail_set):
            scored = HubTools.score_hubs.func(["Denver"])
        self.assertEqual(scored[0].score, 0)
        self.assertEqual(scored[0].factors[0].name, "Snow days")
        self.assertFalse(scored[0].refreshed)
        self.assertEqual(drain_score_alerts(), [])

    def test_missing_scored_at_is_refreshed(self):
        drain_score_alerts()
        doc = {
            "city": "Denver", "city_key": "denver", "state_code": "CO", "region": "West",
            "score": 0,
            "location": {"latitude": 39.7, "longitude": -104.9, "state": "Colorado", "county": "Denver"},
        }
        saved = {}

        def find_one(query):
            return doc if query.get("city_key") == "denver" else None

        def set_fields(query, fields, upsert=False):
            saved.update(fields)

        weather = WeatherHistory(
            source="t", latitude=0, longitude=0, start_date="2025-01-01", end_date="2025-12-31",
            days=365, snow_days=0, freezing_days=0, heavy_rain_days=0, high_wind_days=0,
            snow_days_pct=0, freezing_days_pct=0, heavy_rain_days_pct=10, high_wind_days_pct=0,
            total_snowfall_cm=0, heavy_rain_threshold_mm=25, high_wind_threshold_kmh=60, freezing_threshold_c=0,
        )
        disasters = DisasterHistory(
            source="t", state="CO", county="Denver", since_year=date.today().year,
            total_disasters=4, by_incident_type={"Hurricane": 4},
        )
        alerts = ActiveAlerts(
            source="t", latitude=0, longitude=0, active_alert_count=1,
            alerts=[Alert(event="Hurricane Warning", severity="Extreme", headline=None, expires=None)],
        )

        class Call:
            def __init__(self, value):
                self.value = value

            def invoke(self, args):
                return [self.value]

        with patch("agent.tools.hub_tools.DbTools.find_one", find_one), \
             patch("agent.tools.hub_tools.DbTools.set_fields", set_fields), \
             patch("agent.tools.hub_tools.WeatherTools.get_weather_history", Call(weather)), \
             patch("agent.tools.hub_tools.WeatherTools.get_disaster_history", Call(disasters)), \
             patch("agent.tools.hub_tools.WeatherTools.get_active_alerts", Call(alerts)):
            scored = HubTools.score_hubs.func(["Denver"])

        self.assertEqual(scored[0].score, 65.0)
        self.assertTrue(scored[0].refreshed)
        self.assertEqual(saved["score"], 65.0)
        self.assertTrue(saved["factors"])
        self.assertIsInstance(saved["scored_at"], datetime)
        self.assertEqual(drain_score_alerts(), [{
            "type": "score_alert", "city": "Denver", "previous": 0.0, "score": 65.0,
        }])

    def test_hub_descriptions_are_one_sentence(self):
        descriptions = [
            HubTools.list_hubs.description,
            HubTools.score_hubs.description,
            HubTools.set_hub.description,
        ]
        self.assertEqual(len(descriptions), 3)
        self.assertTrue(all(len(description) < 160 for description in descriptions))
