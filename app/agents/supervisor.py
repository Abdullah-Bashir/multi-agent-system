# app/agents/supervisor_graph.py
from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.types import Command

from .state import MultiAgentState
from .sales_agent import create_sales_agent
from .support_agent import create_support_agent

# --- Supervisor structured output schema ---
class SupervisorDecision(BaseModel):
    """The supervisor's routing decision."""
    next_agent: Literal["sales", "support", "FINISH"] = Field(
        description="Which agent should handle the request, or FINISH to end."
    )
    reasoning: str = Field(description="Brief reasoning for the routing decision.")


SUPERVISOR_PROMPT = """You are a supervisor managing a team of specialists.

Available specialists:
- **sales**: Handles NEW customer inquiries, service questions, and lead qualification/creation.
- **support**: Handles EXISTING lead status inquiries. Requires a tracking code (LEAD-XXXXXX).

## Routing Rules
1. If the user asks about services, pricing, or wants to get started → route to **sales**.
2. If the user provides a tracking code or asks about their existing lead status → route to **support**.
3. If the request is ambiguous, ask a clarifying question instead of routing.
4. If the conversation has reached a natural conclusion (lead created, status provided, or user says thanks) → route to **FINISH**.

Respond with a structured decision.
"""


async def supervisor_node(state: MultiAgentState) -> Command[Literal["sales", "support", "__end__"]]:
    """Supervisor decides which agent should handle the request next."""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).with_structured_output(SupervisorDecision)

    messages = [SystemMessage(content=SUPERVISOR_PROMPT)] + list(state["messages"])

    decision: SupervisorDecision = await llm.ainvoke(messages)

    if decision.next_agent == "FINISH":
        # Return final response directly if supervisor decides to finish
        final_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
        final_prompt = [
            SystemMessage(content="You are a helpful assistant. Provide a concise final response to the user based on the conversation history."),
            *state["messages"],
        ]
        response = await final_llm.ainvoke(final_prompt)
        return Command(
            goto=END,
            update={
                "messages": [response],
                "active_agent": None,
                "iteration_count": state["iteration_count"] + 1,
            },
        )

    # Route to specialist
    return Command(
        goto=decision.next_agent,
        update={"active_agent": decision.next_agent},
    )


async def sales_node(state: MultiAgentState) -> Command[Literal["supervisor"]]:
    """Sales agent node — delegates to ReAct agent, returns to supervisor."""
    agent = create_sales_agent(ChatOpenAI(model="gpt-4o-mini", temperature=0.3))
    result = await agent.ainvoke({"messages": state["messages"]})
    # Take only the last AI message from the agent's output
    last_msg = result["messages"][-1]
    return Command(
        goto="supervisor",
        update={
            "messages": [last_msg],
            "iteration_count": state["iteration_count"] + 1,
        },
    )


async def support_node(state: MultiAgentState) -> Command[Literal["supervisor"]]:
    """Support agent node — delegates to ReAct agent, returns to supervisor."""
    agent = create_support_agent(ChatOpenAI(model="gpt-4o-mini", temperature=0.3))
    result = await agent.ainvoke({"messages": state["messages"]})
    last_msg = result["messages"][-1]
    return Command(
        goto="supervisor",
        update={
            "messages": [last_msg],
            "iteration_count": state["iteration_count"] + 1,
        },
    )


def build_agent_graph(checkpointer):
    graph = StateGraph(MultiAgentState)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("sales", sales_node)
    graph.add_node("support", support_node)
    graph.set_entry_point("supervisor")
    return graph.compile(checkpointer=checkpointer)   # ← THE FIX