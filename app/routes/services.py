from fastapi import APIRouter, HTTPException, status, Response
from typing import List
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ReturnDocument

from database.mongodb import get_db
from models.service import ServiceModel, ServiceCreate, ServiceUpdate


router = APIRouter(prefix="/api/services", tags=["Services"])


def _to_object_id(service_id: str) -> ObjectId:
    try:
        return ObjectId(service_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid service ID format",
        )


@router.get("/", response_model=List[ServiceModel])
async def get_all_services(skip: int = 0, limit: int = 50):
    db = await get_db()
    services = (
        await db.services.find().skip(skip).limit(limit).to_list(length=limit)
    )
    return [ServiceModel(**s) for s in services]


# ⚠️ Keep /active ABOVE /{service_id}
@router.get("/active", response_model=List[ServiceModel])
async def get_active_services():
    db = await get_db()
    services = await db.services.find({"active": True}).to_list(length=100)
    return [ServiceModel(**s) for s in services]


@router.get("/{service_id}", response_model=ServiceModel)
async def get_service(service_id: str):
    db = await get_db()
    service = await db.services.find_one({"_id": _to_object_id(service_id)})
    if not service:
        raise HTTPException(404, f"Service with ID {service_id} not found")
    return ServiceModel(**service)


@router.post("/", response_model=ServiceModel, status_code=status.HTTP_201_CREATED)
async def create_service(service: ServiceCreate):
    db = await get_db()
    service_data = service.model_dump()
    service_data["created_at"] = datetime.now(timezone.utc)
    result = await db.services.insert_one(service_data)
    created_service = await db.services.find_one({"_id": result.inserted_id})
    return ServiceModel(**created_service)


@router.patch("/{service_id}", response_model=ServiceModel)
async def update_service(service_id: str, update: ServiceUpdate):
    db = await get_db()
    update_data = update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(400, "No fields to update")

    update_data["updated_at"] = datetime.now(timezone.utc)

    result = await db.services.find_one_and_update(
        {"_id": _to_object_id(service_id)},
        {"$set": update_data},
        return_document=ReturnDocument.AFTER,
    )
    if not result:
        raise HTTPException(404, f"Service with ID {service_id} not found")
    return ServiceModel(**result)


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(service_id: str):
    db = await get_db()
    result = await db.services.delete_one({"_id": _to_object_id(service_id)})
    if result.deleted_count == 0:
        raise HTTPException(404, f"Service with ID {service_id} not found")
    return Response(status_code=204)