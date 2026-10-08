import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class ScoreAlertUiTests(unittest.TestCase):
    def test_alerts_sit_beside_the_chat_and_vanish(self):
        app = (ROOT / "weather-app" / "src" / "App.tsx").read_text(encoding="utf-8")
        panel = (ROOT / "weather-app" / "src" / "components" / "ScoreAlerts.tsx").read_text(encoding="utf-8")
        chat = (ROOT / "weather-app" / "src" / "components" / "ChatDisplay.tsx").read_text(encoding="utf-8")
        self.assertIn("event.type !== 'score_alert'", app)
        self.assertIn("ALERT_MS", app)
        self.assertIn("bg-yellow-200", panel)
        self.assertIn("overflow-y-auto", panel)
        self.assertIn("list.scrollTop = list.scrollHeight", panel)
        self.assertNotIn("scrollIntoView", panel)
        self.assertIn("messages", chat.split("useEffect")[1])
