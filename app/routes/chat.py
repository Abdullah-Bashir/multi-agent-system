# app/routes/chat.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from app.agents.supervisor_graph import build_agent_graph
from app.agents.state import MultiAgentState

router = APIRouter(prefix="/api", tags=["Chat"])

# In-memory checkpointer for short-term conversation memory
# Swap with MongoDB checkpointer for production persistence[citation:4]
_checkpointer = MemorySaver()
_graph = build_agent_graph(checkpointer=_checkpointer)


class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"
    user_id: Optional[str] = None


@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Send a message to the multi-agent system and receive a streaming response."""
    config = {"configurable": {"thread_id": request.thread_id}}

    initial_state: MultiAgentState = {
        "messages": [HumanMessage(content=request.message)],
        "active_agent": None,
        "tracking_code": None,
        "iteration_count": 0,
    }

    async def event_generator():

        # Giving our graph system the user response - Stream tokens from the graph
        async for event in _graph.astream_events(
            initial_state,
            config=config,
            version="v2",
        ):
            kind = event["event"]
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    yield content

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )


@router.get("/chat/history/{thread_id}")
async def get_chat_history(thread_id: str):
    """Retrieve the conversation history for a thread."""
    config = {"configurable": {"thread_id": thread_id}}
    state = await _graph.aget_state(config)
    if not state or not state.values.get("messages"):
        raise HTTPException(404, f"No history found for thread {thread_id}")

    return [
        {
            "role": msg.type,
            "content": msg.content,
        }
        for msg in state.values["messages"]
    ]