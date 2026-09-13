from fastapi import APIRouter, HTTPException, status, Response
from typing import List
from datetime import datetime, timezone
import secrets
import string

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ReturnDocument

from database.mongodb import get_db
from models.lead import LeadModel, LeadCreate, LeadStatusUpdate

router = APIRouter(prefix="/api/leads", tags=["Leads"])

ALPHABET = string.ascii_uppercase + string.digits

def generate_tracking_code() -> str:
    return "LEAD-" + "".join(secrets.choice(ALPHABET) for _ in range(6))


async def _unique_tracking_code(db) -> str:
    for _ in range(5):
        code = generate_tracking_code()
        if not await db.leads.find_one({"tracking_code": code}, {"_id": 1}):
            return code
    raise HTTPException(500, "Could not generate unique tracking code")


@router.get("/", response_model=List[LeadModel])
async def get_all_leads():
    db = await get_db()
    leads = (
        await db.leads
        .find()
        .sort("created_at", -1)
        .to_list()
    )
    return [LeadModel(**lead) for lead in leads]


@router.get("/{tracking_code}", response_model=LeadModel)
async def get_lead_by_tracking(tracking_code: str):
    db = await get_db()
    lead = await db.leads.find_one({"tracking_code": tracking_code})
    if not lead:
        raise HTTPException(404, f"Lead with tracking code {tracking_code} not found")
    return LeadModel(**lead)


@router.post("/", response_model=LeadModel, status_code=status.HTTP_201_CREATED)
async def create_lead(lead: LeadCreate):
    db = await get_db()

    # Validate service exists
    try:
        service_oid = ObjectId(lead.service_id)
    except InvalidId:
        raise HTTPException(400, "Invalid service_id format")
    if not await db.services.find_one({"_id": service_oid}):
        raise HTTPException(400, "Service not found")

    lead_data = lead.model_dump()
    lead_data["tracking_code"] = await _unique_tracking_code(db)
    lead_data["status"] = "pending"
    lead_data["created_at"] = datetime.now(timezone.utc)

    result = await db.leads.insert_one(lead_data)
    created_lead = await db.leads.find_one({"_id": result.inserted_id})
    return LeadModel(**created_lead)


@router.patch("/{tracking_code}/status", response_model=LeadModel)
async def update_lead_status(tracking_code: str, update: LeadStatusUpdate):
    db = await get_db()
    result = await db.leads.find_one_and_update(
        {"tracking_code": tracking_code},
        {
            "$set": {
                "status": update.status.value,
                "updated_at": datetime.now(timezone.utc),
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    if not result:
        raise HTTPException(404, f"Lead with tracking code {tracking_code} not found")
    return LeadModel(**result)


@router.delete("/{tracking_code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(tracking_code: str):
    db = await get_db()
    result = await db.leads.delete_one({"tracking_code": tracking_code})
    if result.deleted_count == 0:
        raise HTTPException(404, f"Lead with tracking code {tracking_code} not found")
    return Response(status_code=204)