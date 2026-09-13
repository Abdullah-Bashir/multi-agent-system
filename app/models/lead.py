from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from datetime import datetime, timezone
from typing import Optional
from enum import Enum
from bson import ObjectId

class LeadStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    declined = "declined"


class CustomerInfo(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    company: Optional[str] = None


class LeadBase(BaseModel):
    tracking_code: str
    customer: CustomerInfo
    service_id: str
    requirements: str
    budget: float
    timeline: str
    status: LeadStatus = LeadStatus.pending


class LeadCreate(LeadBase):
    pass


class LeadModel(LeadBase):
    id: str = Field(alias="_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

    @field_validator("id", mode="before")
    @classmethod
    def convert_objectid_to_str(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v


class LeadStatusUpdate(BaseModel):
    status: LeadStatus



