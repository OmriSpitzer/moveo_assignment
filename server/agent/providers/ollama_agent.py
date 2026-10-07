import os
from typing import Iterator, Sequence
from dotenv import load_dotenv
from langchain.agents import create_agent
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
        stream(messages: Sequence[BaseMessage], thread_id: str | None = None) -> Iterator[dict]:
            Stream a response from the agent
"""

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
            system_prompt=SYSTEM_PROMPT,
            tools=HubTools.get_tools() + LocationTools.get_tools() + WeatherTools.get_tools()
        )

    # Get a response from the agent
    def get_response(self, messages: Sequence[BaseMessage], thread_id: str | None = None) -> str:
        if not messages:
            raise ValueError("messages must not be empty")
        
        # stream the response from the agent
        for event in self.stream(messages, thread_id):
            # check if the event is an answer
            if event["type"] == "answer":
                return Answer(**event["answer"])

            # check if the event is an error
            elif event["type"] == "error":
                return ERROR_ANSWER(event["message"], self.model, messages[-1].content)

        # return an error answer if the agent finished without a structured answer
        return ERROR_ANSWER("agent finished without a structured answer", self.model, messages[-1].content)

    # Stream a response from the agent
    def stream(self, messages: Sequence[BaseMessage], thread_id: str | None = None) -> Iterator[dict]:
        if not messages:
            raise ValueError("messages must not be empty")
        
        # create a new thread id if one is not provided
        thread_id = thread_id or str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        answer = None
        plain_text = None
        failure_reason = "agent finished without a structured answer"

        # get the prior messages from the agent
        prior = self._agent.get_state({"configurable": {"thread_id": thread_id}}).values.get("messages")
        stream_messages = [messages[-1]] if prior else list(messages)
        
        # stream the response from the agent
        for chunk in self._agent.stream(
            {"messages": stream_messages, "timestamp": timestamp},
            config={"configurable": {"thread_id": thread_id}},
            stream_mode="updates",
        ):
            for node, update in chunk.items():
                if not isinstance(update, dict):
                    continue

                # process the messages
                for message in update.get("messages", []):
                    if isinstance(message, AIMessage):
                        # string answer from the agent with no tool calls
                        if not message.tool_calls and str(message.content).strip():
                            if node == "model":
                                plain_text = str(message.content).strip()
                            else:
                                failure_reason = f"agent stopped: {message.content}"
                                plain_text = None

                        # stream the tool calls
                        for call in message.tool_calls:
                            if call["name"] != LLMAnswer.__name__:
                                yield {"type": "tool_call", "id": call["id"], "name": call["name"], "args": call["args"]}
                    
                    # check if the agent returned a tool result
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

                # check if the agent returned a structured answer
                if isinstance(update.get("structured_response"), LLMAnswer):
                    answer = Answer(
                        timestamp=timestamp,
                        model=self.model,
                        prompt=messages[-1].content,
                        answer=update["structured_response"].answer,
                    )

        # check if the agent returned a plain text answer
        if answer is None and plain_text:
            answer = Answer(
                timestamp=timestamp,
                model=self.model,
                prompt=messages[-1].content,
                answer=plain_text,
            )
        
        # no answer -> stream an error
        if answer is None:
            yield {"type": "error", "message": failure_reason}
            return
        yield {"type": "answer", "answer": answer.model_dump()}

