"""RBAC permission checking service — validate user permissions at runtime."""
from __future__ import annotations

import functools
import streamlit as st
from sqlalchemy import select, text

from app.core.db_sync import get_sync_db
from app.modules.permissions.model import (
    ROLE_PERMISSION_MATRIX, make_permission_code,
    ACTION_VIEW, ACTION_CREATE, ACTION_UPDATE, ACTION_DELETE,
    ACTION_EXPORT, ACTION_MANAGE, ACTION_ADMIN,
)


def get_user_role_codes(user_email: str) -> list[str]:
    """Get all role codes for a user from user_roles table."""
    try:
        with get_sync_db() as db:
            rows = db.execute(text("""
                SELECT r.role_code FROM roles r
                JOIN user_roles ur ON ur.role_id = r.id
                JOIN users u ON u.id = ur.user_id
                WHERE u.email = :email
                AND ur.is_deleted = false
                AND r.is_deleted = false
            """), {"email": user_email}).fetchall()
            return [r[0] for r in rows]
    except Exception:
        return []


def has_permission(user_email: str, module: str, action: str) -> bool:
    """Check if user has permission for module+action. Falls back to role column."""
    from app.modules.auth.session import get_current_user
    user = get_current_user()
    if not user:
        return False

    # System admin always has full access
    if user.role in ("super_admin", "SYSTEM_ADMIN"):
        return True

    # Check role-based permissions from matrix
    role_codes = get_user_role_codes(user_email)

    # If no role_codes in new table, fall back to legacy role column
    if not role_codes:
        legacy_map = {
            "super_admin": "SYSTEM_ADMIN",
            "province_admin": "PROVINCE_ADMIN",
            "district_admin": "DISTRICT_ADMIN",
            "subdistrict_admin": "SUBDISTRICT_ADMIN",
            "volunteer": "VOLUNTEER",
            "viewer": "VIEWER",
        }
        role_codes = [legacy_map.get(user.role, "VIEWER")]

    for role_code in role_codes:
        allowed = ROLE_PERMISSION_MATRIX.get(role_code, {}).get(module, [])
        if action in allowed:
            return True
    return False


def require_permission(module: str, action: str):
    """Streamlit guard — stops page if user lacks permission."""
    from app.modules.auth.session import get_current_user
    user = get_current_user()
    if not user:
        st.error("Not authenticated.")
        st.stop()
    if not has_permission(user.email, module, action):
        st.error(f"Access denied: you need {action} permission on {module}.")
        st.stop()


def get_user_scope(user_email: str) -> dict:
    """Get the area scope for a user."""
    try:
        with get_sync_db() as db:
            row = db.execute(text("""
                SELECT province_code, district_code, subdistrict_code, village_code
                FROM user_scopes us
                JOIN users u ON u.id = us.user_id
                WHERE u.email = :email
                AND us.is_deleted = false
                ORDER BY us.created_at DESC
                LIMIT 1
            """), {"email": user_email}).fetchone()
            if row:
                return {
                    "province": row[0], "district": row[1],
                    "subdistrict": row[2], "village": row[3],
                }
    except Exception:
        pass
    return {}


def seed_roles_and_permissions(db) -> None:
    """Seed default roles and permissions. Safe to call multiple times."""
    from app.modules.roles.model import Role, ALL_ROLES
    from app.modules.permissions.model import Permission, RolePermission, MODULES, ACTIONS

    # Seed roles
    role_map = {}
    for code, name_th, name_en in ALL_ROLES:
        existing = db.execute(
            select(Role).where(Role.role_code == code)
        ).scalar_one_or_none()
        if not existing:
            role = Role(
                role_code=code, role_name_th=name_th, role_name_en=name_en,
                created_by="system", updated_by="system",
            )
            db.add(role)
            db.flush()
            role_map[code] = role.id
        else:
            role_map[code] = existing.id

    # Seed permissions
    perm_map = {}
    for module in MODULES:
        for action in ACTIONS:
            code = make_permission_code(module, action)
            existing = db.execute(
                select(Permission).where(Permission.permission_code == code)
            ).scalar_one_or_none()
            if not existing:
                perm = Permission(
                    permission_code=code, module_name=module, action=action,
                    created_by="system", updated_by="system",
                )
                db.add(perm)
                db.flush()
                perm_map[code] = perm.id
            else:
                perm_map[code] = existing.id

    # Seed role-permission mappings
    for role_code, module_actions in ROLE_PERMISSION_MATRIX.items():
        role_id = role_map.get(role_code)
        if not role_id:
            continue
        for module, actions in module_actions.items():
            for action in actions:
                perm_code = make_permission_code(module, action)
                perm_id = perm_map.get(perm_code)
                if not perm_id:
                    continue
                existing = db.execute(
                    select(RolePermission).where(
                        RolePermission.role_id == role_id,
                        RolePermission.permission_id == perm_id,
                    )
                ).scalar_one_or_none()
                if not existing:
                    db.add(RolePermission(
                        role_id=role_id, permission_id=perm_id,
                        created_by="system", updated_by="system",
                    ))

    db.commit()
