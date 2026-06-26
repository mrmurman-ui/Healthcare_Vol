"""Permissions — permission codes, role-permission matrix."""
from __future__ import annotations

import uuid
from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import UUIDBase

# ── Actions ───────────────────────────────────────────────────────────────────
ACTION_VIEW    = "VIEW"
ACTION_CREATE  = "CREATE"
ACTION_UPDATE  = "UPDATE"
ACTION_DELETE  = "DELETE"
ACTION_APPROVE = "APPROVE"
ACTION_EXPORT  = "EXPORT"
ACTION_MANAGE  = "MANAGE"
ACTION_ADMIN   = "ADMIN"

ACTIONS = [ACTION_VIEW, ACTION_CREATE, ACTION_UPDATE, ACTION_DELETE,
           ACTION_APPROVE, ACTION_EXPORT, ACTION_MANAGE, ACTION_ADMIN]

# ── Modules ───────────────────────────────────────────────────────────────────
MODULES = [
    "users", "volunteers", "citizens", "health_profiles", "assessments",
    "cases", "home_visits", "referrals", "followups", "tasks", "gis",
    "heatmaps", "analytics", "reports", "community_projects",
    "administration", "audit", "ai_assistant", "monitoring",
]

# ── Default permission matrix per role ────────────────────────────────────────
# role_code -> {module -> [actions]}
ROLE_PERMISSION_MATRIX: dict[str, dict[str, list[str]]] = {
    "SYSTEM_ADMIN": {m: ACTIONS for m in MODULES},
    "PROVINCE_ADMIN": {m: [ACTION_VIEW, ACTION_CREATE, ACTION_UPDATE,
                            ACTION_EXPORT, ACTION_MANAGE] for m in MODULES},
    "DISTRICT_ADMIN": {m: [ACTION_VIEW, ACTION_CREATE, ACTION_UPDATE,
                            ACTION_EXPORT] for m in MODULES},
    "SUBDISTRICT_ADMIN": {m: [ACTION_VIEW, ACTION_CREATE, ACTION_UPDATE,
                               ACTION_EXPORT] for m in MODULES},
    "COMMUNITY_LEADER": {
        "citizens": [ACTION_VIEW],
        "home_visits": [ACTION_VIEW],
        "tasks": [ACTION_VIEW, ACTION_CREATE],
        "community_projects": [ACTION_VIEW, ACTION_CREATE, ACTION_UPDATE],
        **{m: [ACTION_VIEW] for m in MODULES
           if m not in ["citizens", "home_visits", "tasks", "community_projects"]},
    },
    "VOL_COORDINATOR": {
        "volunteers": [ACTION_VIEW, ACTION_CREATE, ACTION_UPDATE, ACTION_MANAGE],
        "citizens": [ACTION_VIEW, ACTION_CREATE, ACTION_UPDATE],
        "home_visits": [ACTION_VIEW, ACTION_CREATE, ACTION_UPDATE],
        "tasks": [ACTION_VIEW, ACTION_CREATE, ACTION_UPDATE, ACTION_MANAGE],
        "followups": [ACTION_VIEW, ACTION_CREATE, ACTION_UPDATE],
        "referrals": [ACTION_VIEW, ACTION_CREATE],
        "analytics": [ACTION_VIEW, ACTION_EXPORT],
        "reports": [ACTION_VIEW, ACTION_EXPORT],
        **{m: [ACTION_VIEW] for m in MODULES
           if m not in ["volunteers", "citizens", "home_visits", "tasks",
                        "followups", "referrals", "analytics", "reports"]},
    },
    "VOLUNTEER": {
        "citizens": [ACTION_VIEW, ACTION_CREATE, ACTION_UPDATE],
        "health_profiles": [ACTION_VIEW, ACTION_CREATE, ACTION_UPDATE],
        "assessments": [ACTION_VIEW, ACTION_CREATE, ACTION_UPDATE],
        "home_visits": [ACTION_VIEW, ACTION_CREATE, ACTION_UPDATE],
        "referrals": [ACTION_VIEW, ACTION_CREATE],
        "followups": [ACTION_VIEW, ACTION_CREATE],
        "tasks": [ACTION_VIEW, ACTION_UPDATE],
        **{m: [ACTION_VIEW] for m in MODULES
           if m not in ["citizens", "health_profiles", "assessments",
                        "home_visits", "referrals", "followups", "tasks"]},
    },
    "PHYSICIAN_ADVISOR": {
        "health_profiles": [ACTION_VIEW],
        "assessments": [ACTION_VIEW],
        "analytics": [ACTION_VIEW, ACTION_EXPORT],
        "heatmaps": [ACTION_VIEW],
        "reports": [ACTION_VIEW, ACTION_EXPORT],
        "monitoring": [ACTION_VIEW],
        **{m: [] for m in MODULES
           if m not in ["health_profiles", "assessments", "analytics",
                        "heatmaps", "reports", "monitoring"]},
    },
    "PUBLIC_HEALTH_OFFICER": {
        **{m: [ACTION_VIEW, ACTION_EXPORT] for m in MODULES},
    },
    "VIEWER": {
        **{m: [ACTION_VIEW] for m in MODULES},
    },
}


class Permission(UUIDBase):
    __tablename__ = "permissions"

    permission_code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    module_name: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)


class RolePermission(UUIDBase):
    __tablename__ = "role_permissions"

    role_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)


def make_permission_code(module: str, action: str) -> str:
    return f"{module.upper()}_{action.upper()}"
