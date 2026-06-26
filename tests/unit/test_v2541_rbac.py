"""Tests for V2.54.1 — RBAC, Roles, Permissions, User Management."""
from __future__ import annotations

import pytest
from datetime import date


# ── Role definitions ──────────────────────────────────────────────────────────

def test_all_roles_defined():
    from app.modules.roles.model import ALL_ROLES, ROLE_SYSTEM_ADMIN, ROLE_VIEWER
    codes = [r[0] for r in ALL_ROLES]
    assert ROLE_SYSTEM_ADMIN in codes
    assert ROLE_VIEWER in codes
    assert len(ALL_ROLES) == 10


def test_roles_have_thai_and_english():
    from app.modules.roles.model import ALL_ROLES
    for code, name_th, name_en in ALL_ROLES:
        assert code, "Role code must not be empty"
        assert name_th, f"Thai name missing for {code}"
        assert name_en, f"English name missing for {code}"


# ── Permission matrix ─────────────────────────────────────────────────────────

def test_system_admin_has_all_permissions():
    from app.modules.permissions.model import ROLE_PERMISSION_MATRIX, ACTIONS, MODULES
    admin_perms = ROLE_PERMISSION_MATRIX.get("SYSTEM_ADMIN", {})
    for module in MODULES:
        actions = admin_perms.get(module, [])
        assert set(ACTIONS).issubset(set(actions)), \
            f"System admin missing actions for {module}"


def test_physician_advisor_read_only():
    from app.modules.permissions.model import ROLE_PERMISSION_MATRIX, ACTION_CREATE, ACTION_DELETE
    advisor = ROLE_PERMISSION_MATRIX.get("PHYSICIAN_ADVISOR", {})
    for module, actions in advisor.items():
        assert ACTION_CREATE not in actions, f"Advisor should not CREATE in {module}"
        assert ACTION_DELETE not in actions, f"Advisor should not DELETE in {module}"


def test_volunteer_cannot_delete():
    from app.modules.permissions.model import ROLE_PERMISSION_MATRIX, ACTION_DELETE
    vol = ROLE_PERMISSION_MATRIX.get("VOLUNTEER", {})
    for module, actions in vol.items():
        assert ACTION_DELETE not in actions, f"Volunteer should not DELETE in {module}"


def test_viewer_only_view():
    from app.modules.permissions.model import ROLE_PERMISSION_MATRIX, ACTION_VIEW, ACTIONS
    viewer = ROLE_PERMISSION_MATRIX.get("VIEWER", {})
    for module, actions in viewer.items():
        for action in actions:
            assert action == ACTION_VIEW, f"Viewer has unexpected action {action} in {module}"


def test_permission_code_format():
    from app.modules.permissions.model import make_permission_code
    code = make_permission_code("citizens", "view")
    assert code == "CITIZENS_VIEW"


def test_all_roles_in_matrix():
    from app.modules.roles.model import ALL_ROLES
    from app.modules.permissions.model import ROLE_PERMISSION_MATRIX
    for role_code, _, _ in ALL_ROLES:
        assert role_code in ROLE_PERMISSION_MATRIX, \
            f"Role {role_code} missing from permission matrix"


# ── User scope ────────────────────────────────────────────────────────────────

def test_scope_level_national():
    from app.modules.user_scopes.model import UserScope
    scope = UserScope(user_id=None)
    assert scope.scope_level == "national"


def test_scope_level_province():
    from app.modules.user_scopes.model import UserScope
    scope = UserScope(user_id=None, province_code="CNX")
    assert scope.scope_level == "province"


def test_scope_level_village():
    from app.modules.user_scopes.model import UserScope
    scope = UserScope(user_id=None, province_code="CNX",
                      district_code="D1", subdistrict_code="S1", village_code="V1")
    assert scope.scope_level == "village"


def test_scope_can_access_within_scope():
    from app.modules.user_scopes.model import UserScope
    scope = UserScope(user_id=None, province_code="CNX", district_code="D1")
    assert scope.can_access(province="CNX", district="D1") is True


def test_scope_denies_outside():
    from app.modules.user_scopes.model import UserScope
    scope = UserScope(user_id=None, province_code="CNX")
    assert scope.can_access(province="BKK") is False


def test_national_scope_allows_all():
    from app.modules.user_scopes.model import UserScope
    scope = UserScope(user_id=None)
    assert scope.can_access(province="BKK", district="D1") is True


# ── User profile ──────────────────────────────────────────────────────────────

def test_user_statuses_defined():
    from app.modules.user_management.model import (
        USER_STATUS_ACTIVE, USER_STATUS_INACTIVE,
        USER_STATUS_SUSPENDED, USER_STATUS_LOCKED, ALL_STATUSES
    )
    assert USER_STATUS_ACTIVE in ALL_STATUSES
    assert USER_STATUS_SUSPENDED in ALL_STATUSES
    assert len(ALL_STATUSES) == 4


def test_hard_delete_prohibited():
    """Verify soft delete policy — no hard delete in model."""
    from app.modules.user_management.model import UserProfile
    import inspect
    source = inspect.getsource(UserProfile)
    assert "is_deleted" in source
    assert "deleted_at" in source
    assert "deleted_by" in source


# ── Password generation ───────────────────────────────────────────────────────

def test_temp_password_length():
    from app.modules.user_management.page import _generate_temp_password
    pwd = _generate_temp_password(12)
    assert len(pwd) == 12


def test_temp_password_unique():
    from app.modules.user_management.page import _generate_temp_password
    pwd1 = _generate_temp_password()
    pwd2 = _generate_temp_password()
    assert pwd1 != pwd2


# ── Integration tests ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_role(session):
    from app.modules.roles.model import Role
    role = Role(
        role_code="TEST_ROLE",
        role_name_th="บทบาททดสอบ",
        role_name_en="Test Role",
        created_by="system", updated_by="system",
    )
    session.add(role)
    await session.flush()
    await session.refresh(role)
    assert role.id is not None
    assert role.role_code == "TEST_ROLE"


@pytest.mark.asyncio
async def test_create_permission(session):
    from app.modules.permissions.model import Permission
    perm = Permission(
        permission_code="CITIZENS_VIEW",
        module_name="citizens",
        action="VIEW",
        created_by="system", updated_by="system",
    )
    session.add(perm)
    await session.flush()
    await session.refresh(perm)
    assert perm.id is not None
    assert perm.action == "VIEW"


@pytest.mark.asyncio
async def test_create_user_scope(session):
    import uuid
    from app.modules.user_scopes.model import UserScope
    scope = UserScope(
        user_id=uuid.uuid4(),
        province_code="CNX",
        district_code="MUEANG",
        assigned_by="admin",
        created_by="admin", updated_by="admin",
    )
    session.add(scope)
    await session.flush()
    await session.refresh(scope)
    assert scope.id is not None
    assert scope.province_code == "CNX"


@pytest.mark.asyncio
async def test_create_login_history(session):
    from datetime import datetime, UTC
    from app.modules.login_history.model import LoginHistory
    entry = LoginHistory(
        username="admin",
        login_time=datetime.now(UTC),
        login_result="success",
        created_by="system", updated_by="system",
    )
    session.add(entry)
    await session.flush()
    await session.refresh(entry)
    assert entry.id is not None
    assert entry.login_result == "success"


@pytest.mark.asyncio
async def test_failed_login_tracked(session):
    from app.modules.login_history.model import LoginHistory
    entry = LoginHistory(
        username="hacker@test.com",
        login_result="failed",
        failed_attempts=3,
        created_by="system", updated_by="system",
    )
    session.add(entry)
    await session.flush()
    await session.refresh(entry)
    assert entry.login_result == "failed"
    assert entry.failed_attempts == 3
