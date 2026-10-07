from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from agent.providers.ollama_agent import OllamaAgent
from agent.providers.fake_agent import FakeAgent

class Agent():
    def __init__(self, is_fake:bool = True):
        self.agent = OllamaAgent() if not is_fake else FakeAgent()

    def get_response(self, message: str):
        return self.agent.get_response([HumanMessage(content=message)])

    # messages: chat history as [{"role": "user" | "assistant", "content": str}]
    def stream(self, messages: list[dict], thread_id: str | None = None):
        history: list[BaseMessage] = [
            HumanMessage(content=m["content"]) if m["role"] == "user" else AIMessage(content=m["content"])
            for m in messages
        ]
        return self.agent.stream(history, thread_id)

    
