import uuid
from datetime import datetime
from pydantic import BaseModel, field_validator

from app.shared.enums import UserRole


class UserCreate(BaseModel):
    email: str  # used as username — no email format required
    password: str
    full_name: str
    role: UserRole = UserRole.VIEWER
    province: str | None = None
    district: str | None = None
    subdistrict: str | None = None

    @field_validator("email")
    @classmethod
    def username_not_empty(cls, v: str) -> str:
        v = v.strip().lower()
        if not v:
            raise ValueError("Username cannot be empty")
        return v


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: UserRole | None = None
    province: str | None = None
    district: str | None = None
    subdistrict: str | None = None
    is_active: bool | None = None


class UserRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    province: str | None
    district: str | None
    subdistrict: str | None
    is_active: bool
    created_at: datetime
