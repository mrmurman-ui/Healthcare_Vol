"""Roles — role definitions and role-permission mappings."""
from __future__ import annotations

import uuid
from sqlalchemy import String, Text, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import UUIDBase

# ── Role codes (canonical) ────────────────────────────────────────────────────
ROLE_SYSTEM_ADMIN       = "SYSTEM_ADMIN"
ROLE_PROVINCE_ADMIN     = "PROVINCE_ADMIN"
ROLE_DISTRICT_ADMIN     = "DISTRICT_ADMIN"
ROLE_SUBDISTRICT_ADMIN  = "SUBDISTRICT_ADMIN"
ROLE_COMMUNITY_LEADER   = "COMMUNITY_LEADER"
ROLE_VOL_COORDINATOR    = "VOL_COORDINATOR"
ROLE_VOLUNTEER          = "VOLUNTEER"
ROLE_PHYSICIAN_ADVISOR  = "PHYSICIAN_ADVISOR"
ROLE_PHO                = "PUBLIC_HEALTH_OFFICER"
ROLE_VIEWER             = "VIEWER"

ALL_ROLES = [
    (ROLE_SYSTEM_ADMIN,      "ผู้ดูแลระบบ",           "System Administrator"),
    (ROLE_PROVINCE_ADMIN,    "ผู้ดูแลจังหวัด",         "Province Administrator"),
    (ROLE_DISTRICT_ADMIN,    "ผู้ดูแลอำเภอ",           "District Administrator"),
    (ROLE_SUBDISTRICT_ADMIN, "ผู้ดูแลตำบล",            "Subdistrict Administrator"),
    (ROLE_COMMUNITY_LEADER,  "ผู้นำชุมชน",             "Community Leader"),
    (ROLE_VOL_COORDINATOR,   "ผู้ประสานงานอาสาสมัคร",  "Volunteer Coordinator"),
    (ROLE_VOLUNTEER,         "อาสาสมัครสาธารณสุข",     "Village Health Volunteer"),
    (ROLE_PHYSICIAN_ADVISOR, "แพทย์ที่ปรึกษา",         "Physician Advisor"),
    (ROLE_PHO,               "เจ้าหน้าที่สาธารณสุข",   "Public Health Officer"),
    (ROLE_VIEWER,            "ผู้ดู",                   "Viewer"),
]


class Role(UUIDBase):
    __tablename__ = "roles"

    role_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    role_name_th: Mapped[str] = mapped_column(String(200), nullable=False)
    role_name_en: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)


class UserRole(UUIDBase):
    __tablename__ = "user_roles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
