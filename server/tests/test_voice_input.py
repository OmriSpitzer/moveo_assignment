import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class VoiceInputTests(unittest.TestCase):
    def test_pause_sends_and_a_click_only_stops(self):
        voice = (ROOT / "weather-app" / "src" / "components" / "VoiceInput.tsx").read_text(encoding="utf-8")
        app = (ROOT / "weather-app" / "src" / "App.tsx").read_text(encoding="utf-8")
        pause = voice.split("window.setTimeout(() => {", 1)[1].split("}, PAUSE_MS)", 1)[0]
        stop = voice.split("const stop = () => {", 1)[1].split("return (", 1)[0]
        error = voice.split("recognition.onerror = () => {", 1)[1].split("recognition.onend", 1)[0]
        self.assertLess(pause.index("sendOnEndRef.current = true"), pause.index("recognition.stop()"))
        self.assertLess(stop.index("sendOnEndRef.current = false"), stop.index("recognitionRef.current?.stop()"))
        self.assertLess(error.index("sendOnEndRef.current = false"), error.index("recognition.stop()"))
        self.assertIn("onTranscriptRef.current(spoken, sendNow)", voice)
        self.assertIn("if (!sendNow || isStreaming || !question)", app)
        self.assertIn("void send(question)", app)
