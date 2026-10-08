from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from agent.providers.ollama_agent import OllamaAgent
from agent.providers.fake_agent import FakeAgent

"""
    Agent wrapper class

    Attributes:
        agent: the agent provider

    Methods:
        get_response: get a response from the agent
        stream: stream a response from the agent
"""
class Agent():
    def __init__(self, is_fake:bool = False):
        self.agent = OllamaAgent() if not is_fake else FakeAgent()

    # get a response from the agent
    def get_response(self, message: str):
        return self.agent.get_response([HumanMessage(content=message)])

    # stream a response from the agent
    def stream(self, messages: list[dict], thread_id: str | None = None):
        history: list[BaseMessage] = []
        for msg in messages:
            retrieved = HumanMessage(content=msg["content"]) if msg["role"] == "user" else AIMessage(content=msg["content"])
            history.append(retrieved)
        
        return self.agent.stream(history, thread_id)

    
