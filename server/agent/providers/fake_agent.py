from agent.providers.base_agent import BaseAgent
from typing import Iterator, Sequence
from langchain_core.messages import BaseMessage
from agent.schema.answer import Answer
from datetime import datetime

"""
    Fake agent for testing

    Attributes:
        None
    
    Methods:
        get_response(messages: Sequence[BaseMessage], thread_id: str | None = None) -> str:
            Get a response from the agent
        stream(messages: Sequence[BaseMessage], thread_id: str | None = None) -> Iterator[dict]:
            Stream a response from the agent
"""

class FakeAgent(BaseAgent):
    def __init__(self):
        super().__init__()

    # Get a response from the agent
    def get_response(self, messages: Sequence[BaseMessage], thread_id: str | None = None) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prompt = " ".join([message.content for message in messages])

        return Answer(
            timestamp=timestamp,
            model="fake",
            prompt=prompt,
            answer="fake answer"
        ).model_dump_json(indent=2)

    # Stream a response from the agent
    def stream(self, messages: Sequence[BaseMessage], thread_id: str | None = None) -> Iterator[dict]:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prompt = messages[-1].content if messages else ""

        # yield a fixed tool call, tool result and answer
        yield {"type": "tool_call", "id": "fake-1", "name": "get_hub_risk", "args": {"cities": ["Denver"]}}
        yield {"type": "tool_result", "id": "fake-1", "name": "get_hub_risk", "content": "fake hub risk"}

        # yield the answer
        yield {
            "type": "answer",
            "answer": Answer(timestamp=timestamp, model="fake", prompt=prompt, answer="fake answer").model_dump(),
        }