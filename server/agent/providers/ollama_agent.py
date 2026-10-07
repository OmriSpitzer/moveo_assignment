import os
from typing import Iterator, Sequence
from dotenv import load_dotenv
from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import ModelCallLimitMiddleware
from langchain.agents.structured_output import ToolStrategy
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver
from datetime import datetime
from agent.prompts.ollama_system_prompt import SYSTEM_PROMPT
from agent.providers.base_agent import BaseAgent
import uuid
from agent.schema.answer import Answer, ERROR_ANSWER, LLMAnswer
from agent.tools.hub_tools import HubTools
from agent.tools.location_tools import LocationTools
from agent.tools.weather_tools import WeatherTools

"""
    Ollama agent

    Attributes:
        model: str
        _chat: ChatOllama
        _agent: Agent
    
    Methods:
        get_response(messages: Sequence[BaseMessage], thread_id: str | None = None) -> str:
            Get a response from the agent
"""

# Agent custom state used by the agent
class CustomAgentState(AgentState):
    timestamp: str


def agent_tools():
    return HubTools.get_tools() + LocationTools.get_tools() + WeatherTools.get_tools()

class OllamaAgent(BaseAgent):
    def __init__(self) -> None:
        load_dotenv()
        self._conn = ""
        self.model = os.getenv("MODEL")
        self._chat = ChatOllama(
            model=self.model,
            client_kwargs={"headers": {"Authorization": os.getenv("API_KEY")}},
            base_url=os.getenv("BASE_URL"),
            temperature=0.0,
        )
        self._memory = InMemorySaver()
        self._agent = create_agent(
            self._chat,
            checkpointer=self._memory,
            middleware=[ModelCallLimitMiddleware(run_limit=int(os.getenv("RUN_LIMIT")), exit_behavior="end")],
            response_format=ToolStrategy(LLMAnswer),
            state_schema=CustomAgentState,
            system_prompt=SYSTEM_PROMPT,
            tools=agent_tools()
        )

    # Get a response from the agent
    def get_response(self, messages: Sequence[BaseMessage], thread_id: str | None = None) -> str:
        if not messages:
            raise ValueError("messages must not be empty")
        
        for event in self.stream(messages, thread_id):
            if event["type"] == "answer":
                return Answer(**event["answer"])
            if event["type"] == "error":
                return ERROR_ANSWER(event["message"], self.model, messages[-1].content)
        return ERROR_ANSWER("agent finished without a structured answer", self.model, messages[-1].content)

    # A saved thread already has earlier turns, so only the new message is added
    def _messages_for_turn(self, messages: Sequence[BaseMessage], thread_id: str) -> list[BaseMessage]:
        prior = self._agent.get_state({"configurable": {"thread_id": thread_id}}).values.get("messages")
        return [messages[-1]] if prior else list(messages)

    # Fill the fields the LLM does not produce
    def _to_answer(self, llm_answer: LLMAnswer, timestamp: str, prompt: str) -> Answer:
        return Answer(timestamp=timestamp, model=self.model, prompt=prompt, answer=llm_answer.answer)

    # Stream tool calls and results as they happen, then the final answer
    def stream(self, messages: Sequence[BaseMessage], thread_id: str | None = None) -> Iterator[dict]:
        if not messages:
            raise ValueError("messages must not be empty")

        thread_id = thread_id or str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        answer = None
        plain_text = None
        failure_reason = "agent finished without a structured answer"

        for chunk in self._agent.stream(
            {"messages": self._messages_for_turn(messages, thread_id), "timestamp": timestamp},
            config={"configurable": {"thread_id": thread_id}},
            stream_mode="updates",
        ):
            for node, update in chunk.items():
                if not isinstance(update, dict):
                    continue
                for message in update.get("messages", []):
                    # The structured output arrives as an "LLMAnswer" tool call, which is not a real tool
                    if isinstance(message, AIMessage):
                        # Ollama ignores tool_choice, so the model may answer in plain text instead of LLMAnswer;
                        # plain text from a middleware node is the call limit message, not an answer
                        if not message.tool_calls and str(message.content).strip():
                            if node == "model":
                                plain_text = str(message.content).strip()
                            else:
                                failure_reason = f"agent stopped: {message.content}"
                                plain_text = None
                        for call in message.tool_calls:
                            if call["name"] != LLMAnswer.__name__:
                                yield {"type": "tool_call", "id": call["id"], "name": call["name"], "args": call["args"]}
                    elif isinstance(message, ToolMessage):
                        if message.name != LLMAnswer.__name__:
                            yield {
                                "type": "tool_result",
                                "id": message.tool_call_id,
                                "name": message.name,
                                "content": str(message.content)[:500],
                            }
                        elif message.status == "error" or "error" in str(message.content).lower():
                            failure_reason = f"invalid structured answer: {message.content}"
                if isinstance(update.get("structured_response"), LLMAnswer):
                    answer = self._to_answer(update["structured_response"], timestamp, messages[-1].content)

        if answer is None and plain_text:
            answer = self._to_answer(LLMAnswer.model_validate({"answer": plain_text}), timestamp, messages[-1].content)
        if answer is None:
            yield {"type": "error", "message": failure_reason}
            return
        yield {"type": "answer", "answer": answer.model_dump()}

