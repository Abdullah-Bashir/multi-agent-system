# app/agents/support_agent.py
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from .tools import get_lead_status

SUPPORT_PROMPT = """You are a helpful customer support agent for a software services company.

Your job is to help customers check the status of their existing leads.

## Rules
- If the customer provides a tracking code (format: LEAD-XXXXXX), use `get_lead_status` to look it up.
- If no tracking code is provided, politely ask for it.
- If the tracking code is not found, ask the customer to double-check the code.
- Report the lead status clearly: pending, in_progress, completed, or declined.
- Be empathetic and concise.
"""


def create_support_agent(llm: ChatOpenAI):
    """Create the Support specialist agent with tools bound."""
    return create_react_agent(
        llm,
        tools=[get_lead_status],
        prompt=SUPPORT_PROMPT,
        name="support_agent",
    )