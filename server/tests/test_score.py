import unittest
from datetime import date, datetime, timedelta, timezone

from agent.schema.tool_results import ActiveAlerts, Alert, DisasterHistory, ToolError, WeatherHistory
from agent.scoring.score import ScoreMethod


def weather(rain: float) -> WeatherHistory:
    return WeatherHistory(
        source="t", latitude=0, longitude=0, start_date="2025-01-01", end_date="2025-12-31",
        days=365, snow_days=0, freezing_days=0, heavy_rain_days=0, high_wind_days=0,
        snow_days_pct=0, freezing_days_pct=0, heavy_rain_days_pct=rain, high_wind_days_pct=0,
        total_snowfall_cm=0, heavy_rain_threshold_mm=25, high_wind_threshold_kmh=60, freezing_threshold_c=0,
    )


class ScoreTests(unittest.TestCase):
    def test_score_hub_scales_missing_sections(self):
        disasters = DisasterHistory(
            source="t", state="FL", county=None, since_year=date.today().year,
            total_disasters=4, by_incident_type={"Hurricane": 4},
        )
        alerts = ActiveAlerts(
            source="t", latitude=0, longitude=0, active_alert_count=1,
            alerts=[Alert(event="Hurricane Warning", severity="Extreme", headline=None, expires=None)],
        )
        calm = DisasterHistory(
            source="t", state="CO", county=None, since_year=2000,
            total_disasters=0, by_incident_type={},
        )
        none = ActiveAlerts(source="t", latitude=0, longitude=0, active_alert_count=0, alerts=[])

        high = ScoreMethod.score_hub(weather(10), disasters, alerts)
        low = ScoreMethod.score_hub(weather(0), calm, none)
        partial = ScoreMethod.score_hub(ToolError(source="t", error="down"), disasters, alerts)

        self.assertEqual(high.score, 65.0)
        self.assertEqual(low.score, 0.0)
        self.assertEqual(partial.score, 100.0)
        self.assertEqual(partial.excluded, ["weather"])
        self.assertEqual(
            [factor.name for factor in high.factors],
            ["Snow days", "Freezing days", "Heavy rain days", "High wind days", "FEMA disasters", "Active alerts"],
        )

    def test_score_needs_refresh_after_one_day(self):
        now = datetime.now(timezone.utc)
        self.assertTrue(ScoreMethod.score_needs_refresh(None, now))
        self.assertFalse(ScoreMethod.score_needs_refresh(now - timedelta(hours=1), now))
        self.assertTrue(ScoreMethod.score_needs_refresh(now - timedelta(days=1, seconds=1), now))

    def test_score_methods_are_callable(self):
        self.assertTrue(callable(ScoreMethod.score_hub))
        self.assertTrue(callable(ScoreMethod.score_needs_refresh))
