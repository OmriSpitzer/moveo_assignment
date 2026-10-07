import json
from dataclasses import asdict
from typing import Literal
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from agent.agent import Agent
from agent.tools.hub_tools import HubTools
from dataclasses import dataclass

"""
    Agent routes across the API.

    Routes:
        /: root route
        /health: health check route
        /hubs: get hubs route
        /agent: get agent response route
        /agent/stream: stream agent response route
"""

# create the API router
router = APIRouter()

# create the agent
agent = Agent(is_fake=False)

# Chat message model
class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


# Stream request model
class StreamRequest(BaseModel):
    messages: list[ChatMessage]
    thread_id: str | None = None


# Root route
@router.get("/")
def read_root():
    return {"message": "Hello, World!"}

# Health check route
@router.get("/health")
def health_check():
    return {"message": "OK"}

# Get hubs route
@router.get("/hubs")
def get_hubs():
    return [asdict(hub) for hub in HubTools.list_hubs.invoke({})]

# Get agent response
@router.get("/agent")
def get_agent_response(message: str):
    return agent.get_response(message)

# Stream agent response
@router.post("/agent/stream")
def stream_agent_response(request: StreamRequest):
    def events():
        try:
            for event in agent.stream([m.model_dump() for m in request.messages], request.thread_id):
                yield f"data: {json.dumps(event, default=str)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, default=str)}\n\n"
        yield f"data: {json.dumps({'type': 'done'}, default=str)}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})
