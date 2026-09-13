# app/agents/tools.py
from typing import List, Optional
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
from langchain_core.tools import tool

from database.mongodb import get_db
from models.lead import LeadCreate, CustomerInfo
from models.service import ServiceModel


@tool
async def get_services() -> List[dict]:
    """Retrieve all active services available for lead creation.
    Returns a list of services with id, name, description, and price_from.
    Use this before creating a lead to validate service_id."""
    db = await get_db()
    services = await db.services.find({"active": True}).to_list(length=100)
    return [
        {
            "id": str(s["_id"]),
            "name": s["name"],
            "description": s["description"],
            "price_from": s["price_from"],
        }
        for s in services
    ]


@tool
async def create_lead(
    customer_name: str,
    customer_email: str,
    service_id: str,
    requirements: str,
    budget: float,
    timeline: str,
    phone: Optional[str] = None,
    company: Optional[str] = None,
) -> dict:
    """Create a new lead in the CRM system.

    Args:
        customer_name: Full name of the customer
        customer_email: Valid email address
        service_id: MongoDB ObjectId string of the requested service (validate via get_services first)
        requirements: Detailed description of what the customer needs
        budget: Customer's budget as a number
        timeline: Expected timeline (e.g., "2 weeks", "flexible")
        phone: Optional phone number
        company: Optional company name

    Returns the created lead with tracking_code and status.
    """
    from secrets import choice
    import string

    db = await get_db()

    # Validate service
    try:
        service_oid = ObjectId(service_id)
    except InvalidId:
        return {"error": f"Invalid service_id format: {service_id}"}

    if not await db.services.find_one({"_id": service_oid}):
        return {"error": f"Service not found with id: {service_id}"}

    # Generate unique tracking code
    ALPHABET = string.ascii_uppercase + string.digits
    tracking_code = "LEAD-" + "".join(choice(ALPHABET) for _ in range(6))
    for _ in range(5):
        if not await db.leads.find_one({"tracking_code": tracking_code}, {"_id": 1}):
            break
        tracking_code = "LEAD-" + "".join(choice(ALPHABET) for _ in range(6))

    lead_data = {
        "tracking_code": tracking_code,
        "customer": {
            "name": customer_name,
            "email": customer_email,
            "phone": phone,
            "company": company,
        },
        "service_id": service_id,
        "requirements": requirements,
        "budget": budget,
        "timeline": timeline,
        "status": "pending",
        "created_at": datetime.now(timezone.utc),
        "updated_at": None,
    }

    result = await db.leads.insert_one(lead_data)
    created = await db.leads.find_one({"_id": result.inserted_id})

    return {
        "id": str(created["_id"]),
        "tracking_code": created["tracking_code"],
        "customer": created["customer"],
        "status": created["status"],
        "created_at": created["created_at"].isoformat(),
    }


@tool
async def get_lead_status(tracking_code: str) -> dict:
    """Look up a lead by its tracking code.

    Args:
        tracking_code: The tracking code in format LEAD-XXXXXX

    Returns the lead's full details including status, or an error if not found.
    """
    db = await get_db()
    lead = await db.leads.find_one({"tracking_code": tracking_code})
    if not lead:
        return {"error": f"No lead found with tracking code: {tracking_code}"}

    return {
        "id": str(lead["_id"]),
        "tracking_code": lead["tracking_code"],
        "customer": lead["customer"],
        "service_id": lead["service_id"],
        "requirements": lead["requirements"],
        "budget": lead["budget"],
        "timeline": lead["timeline"],
        "status": lead["status"],
        "created_at": lead["created_at"].isoformat(),
        "updated_at": lead["updated_at"].isoformat() if lead.get("updated_at") else None,
    }