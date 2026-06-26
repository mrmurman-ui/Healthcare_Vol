import uuid
from datetime import datetime

from pydantic import BaseModel

from app.shared.enums import VolunteerStatus


class VolunteerCreate(BaseModel):
    volunteer_code: str
    full_name: str
    phone: str | None = None
    email: str | None = None
    province: str | None = None
    district: str | None = None
    subdistrict: str | None = None
    village: str | None = None
    position: str | None = None
    status: VolunteerStatus = VolunteerStatus.ACTIVE
    photo_url: str | None = None


class VolunteerUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    email: str | None = None
    province: str | None = None
    district: str | None = None
    subdistrict: str | None = None
    village: str | None = None
    position: str | None = None
    status: VolunteerStatus | None = None
    photo_url: str | None = None


class VolunteerRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    volunteer_code: str
    full_name: str
    phone: str | None
    email: str | None
    province: str | None
    district: str | None
    subdistrict: str | None
    village: str | None
    position: str | None
    status: VolunteerStatus
    photo_url: str | None
    created_at: datetime
