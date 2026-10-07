from abc import ABC, abstractmethod
from typing import Iterator, Sequence
from langchain_core.messages import BaseMessage

"""
    Agent interface

    Attributes:
        None
    
    Methods:
        get_response(messages: Sequence[BaseMessage], thread_id: str | None = None) -> str:
            Get a response from the agent
        stream(messages: Sequence[BaseMessage], thread_id: str | None = None) -> Iterator[dict]:
            Stream a response from the agent
"""
class BaseAgent(ABC):
    def __init__(self):
        pass

    # Get a response from the agent
    @abstractmethod
    def get_response(self, messages: Sequence[BaseMessage], thread_id: str | None = None) -> str:
        raise NotImplementedError

    # Stream a response from the agent
    @abstractmethod
    def stream(self, messages: Sequence[BaseMessage], thread_id: str | None = None) -> Iterator[dict]:
        raise NotImplementedError