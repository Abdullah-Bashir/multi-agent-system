# app/agents/state.py
from typing import Annotated, Literal, Optional, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class MultiAgentState(TypedDict):
    """Shared state passed between supervisor and specialist agents."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    # Track which agent last handled the request
    active_agent: Optional[Literal["sales", "support"]]
    # Optional: store extracted tracking code for support
    tracking_code: Optional[str]
    # Iteration guard to prevent infinite supervisor loops
    iteration_count: int