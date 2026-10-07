import inspect
import unittest

from langchain_core.messages import HumanMessage

from agent.providers.fake_agent import FakeAgent
from agent.providers.ollama_agent import OllamaAgent


class StreamTests(unittest.TestCase):
    def test_fake_stream_ends_with_an_answer(self):
        events = list(FakeAgent().stream([HumanMessage(content="hi")]))
        self.assertEqual([event["type"] for event in events], ["tool_call", "tool_result", "answer"])
        self.assertEqual(events[-1]["answer"]["answer"], "fake answer")
        self.assertEqual(events[-1]["answer"]["model"], "fake")

    def test_ollama_stream_builds_answer_in_two_places(self):
        source = inspect.getsource(OllamaAgent.stream)
        self.assertFalse(hasattr(OllamaAgent, "_to_answer"))
        self.assertEqual(source.count("Answer("), 2)
