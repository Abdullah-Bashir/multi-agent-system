from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId


class ServiceBase(BaseModel):
    name: str
    description: str
    price_from: float
    active: bool = True


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price_from: Optional[float] = None
    active: Optional[bool] = None


class ServiceModel(ServiceBase):
    id: str = Field(alias="_id")   
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)  
    )

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