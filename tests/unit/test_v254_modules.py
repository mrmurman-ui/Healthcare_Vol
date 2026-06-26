"""Tests for V2.54 — Settings, Feature Flags, Logging, Error Tracking, Scheduler."""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock


# ── Settings ──────────────────────────────────────────────────────────────────

def test_default_settings_exist():
    from app.modules.settings.service import DEFAULTS
    assert "app_name" in DEFAULTS
    assert "timezone" in DEFAULTS
    assert "min_password_length" in DEFAULTS
    assert "session_timeout_minutes" in DEFAULTS
    assert "max_login_attempts" in DEFAULTS


def test_default_settings_values():
    from app.modules.settings.service import DEFAULTS
    assert int(DEFAULTS["min_password_length"]) >= 6
    assert int(DEFAULTS["max_login_attempts"]) >= 3
    assert DEFAULTS["maintenance_mode"] == "false"


# ── Feature Flags ─────────────────────────────────────────────────────────────

def test_default_flags_exist():
    from app.modules.feature_flags.service import DEFAULT_FLAGS
    keys = [f["key"] for f in DEFAULT_FLAGS]
    assert "ai_assistant" in keys
    assert "gis" in keys
    assert "analytics" in keys
    assert "exports" in keys
    assert "scheduler" in keys


def test_default_flags_have_required_fields():
    from app.modules.feature_flags.service import DEFAULT_FLAGS
    for flag in DEFAULT_FLAGS:
        assert "key" in flag
        assert "name" in flag
        assert "default" in flag
        assert isinstance(flag["default"], bool)


def test_is_enabled_returns_true_for_missing():
    """is_enabled should default to True if flag not in DB."""
    with patch("app.modules.feature_flags.service.get_sync_db") as mock_db:
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=MagicMock(
            execute=MagicMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
        ))
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_db.return_value = mock_ctx
        from app.modules.feature_flags.service import is_enabled
        assert is_enabled("nonexistent_flag") is True


# ── Error Tracking ────────────────────────────────────────────────────────────

def test_capture_error_does_not_raise():
    """capture_error must never raise an exception."""
    from app.modules.error_tracking.service import capture_error
    # Even if DB is down, this should not raise
    try:
        with patch("app.modules.error_tracking.service.get_sync_db",
                   side_effect=Exception("DB down")):
            capture_error("test_module", "Test error message")
    except Exception:
        pytest.fail("capture_error raised an exception — it should be silent")


def test_severity_levels():
    from app.modules.error_tracking.service import SEVERITY_LEVELS
    assert "INFO" in SEVERITY_LEVELS
    assert "WARNING" in SEVERITY_LEVELS
    assert "ERROR" in SEVERITY_LEVELS
    assert "CRITICAL" in SEVERITY_LEVELS


# ── Application Logs ──────────────────────────────────────────────────────────

def test_log_event_does_not_raise():
    """log_event must never crash the application."""
    from app.modules.application_logs.service import log_event
    try:
        with patch("app.modules.application_logs.service.get_sync_db",
                   side_effect=Exception("DB down")):
            log_event("test_module", "Test action")
    except Exception:
        pytest.fail("log_event raised an exception — it should be silent")


def test_log_levels():
    from app.modules.application_logs.service import LOG_LEVELS
    assert "INFO" in LOG_LEVELS
    assert "ERROR" in LOG_LEVELS
    assert "CRITICAL" in LOG_LEVELS


def test_log_modules():
    from app.modules.application_logs.service import LOG_MODULES
    assert "auth" in LOG_MODULES
    assert "ai_assistant" in LOG_MODULES
    assert "reports" in LOG_MODULES


# ── Scheduler ────────────────────────────────────────────────────────────────

def test_scheduled_jobs_defined():
    from app.modules.scheduler.service import SCHEDULED_JOBS
    assert len(SCHEDULED_JOBS) >= 4
    for job in SCHEDULED_JOBS:
        assert "id" in job
        assert "name" in job
        assert "fn" in job
        assert callable(job["fn"])


def test_scheduler_no_celery_no_redis():
    """Scheduler must not import or require Celery or Redis."""
    import inspect
    from app.modules.scheduler import service
    source = inspect.getsource(service)
    assert "celery" not in source.lower()
    assert "redis" not in source.lower()


# ── Versioning ────────────────────────────────────────────────────────────────

def test_version_info():
    from app.modules.versioning.service import VERSION_INFO
    assert "version" in VERSION_INFO
    assert VERSION_INFO["version"] == "2.54"
    assert "modules" in VERSION_INFO
    assert len(VERSION_INFO["modules"]) >= 5


# ── Import Engine ─────────────────────────────────────────────────────────────

def test_validate_volunteers_valid():
    import pandas as pd
    from app.modules.import_engine.service import validate_volunteers
    df = pd.DataFrame([
        {"volunteer_code": "VOL001", "full_name": "Test Vol",
         "phone": "0812345678", "province": "เชียงใหม่"},
    ])
    valid, errors = validate_volunteers(df)
    assert len(valid) == 1
    assert len(errors) == 0


def test_validate_volunteers_missing_code():
    import pandas as pd
    from app.modules.import_engine.service import validate_volunteers
    df = pd.DataFrame([
        {"volunteer_code": "", "full_name": "Test Vol"},
    ])
    valid, errors = validate_volunteers(df)
    assert len(valid) == 0
    assert len(errors) == 1


def test_validate_volunteers_missing_name():
    import pandas as pd
    from app.modules.import_engine.service import validate_volunteers
    df = pd.DataFrame([
        {"volunteer_code": "VOL001", "full_name": ""},
    ])
    valid, errors = validate_volunteers(df)
    assert len(valid) == 0
    assert len(errors) == 1


def test_validate_citizens_valid():
    import pandas as pd
    from app.modules.import_engine.service import validate_citizens
    df = pd.DataFrame([
        {"full_name": "สมชาย ใจดี", "gender": "male", "phone": "0812345678"},
    ])
    valid, errors = validate_citizens(df)
    assert len(valid) == 1
    assert len(errors) == 0


def test_validate_citizens_normalizes_gender():
    import pandas as pd
    from app.modules.import_engine.service import validate_citizens
    df = pd.DataFrame([
        {"full_name": "Test Person", "gender": "UNKNOWN"},
    ])
    valid, errors = validate_citizens(df)
    assert len(valid) == 1
    assert valid[0]["gender"] == "other"


# ── Backup ────────────────────────────────────────────────────────────────────

def test_export_json_structure():
    """Test JSON export returns valid JSON string."""
    import json
    from unittest.mock import MagicMock, patch
    mock_db = MagicMock()
    mock_db.execute.return_value.mappings.return_value.all.return_value = [
        {"id": "1", "name": "Test"}
    ]
    from app.modules.backup_restore.service import export_json
    result = export_json(mock_db, ["volunteers"])
    parsed = json.loads(result)
    assert "volunteers" in parsed


# ── Integration tests ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_system_setting(session):
    from app.modules.settings.service import SystemSetting
    setting = SystemSetting(
        key="test_setting",
        value="test_value",
        description="Test setting",
        created_by="system", updated_by="system",
    )
    session.add(setting)
    await session.flush()
    await session.refresh(setting)
    assert setting.id is not None
    assert setting.key == "test_setting"
    assert setting.value == "test_value"


@pytest.mark.asyncio
async def test_create_feature_flag(session):
    from app.modules.feature_flags.service import FeatureFlag
    flag = FeatureFlag(
        key="test_feature",
        name="Test Feature",
        enabled=True,
        created_by="system", updated_by="system",
    )
    session.add(flag)
    await session.flush()
    await session.refresh(flag)
    assert flag.id is not None
    assert flag.enabled is True


@pytest.mark.asyncio
async def test_toggle_feature_flag(session):
    from app.modules.feature_flags.service import FeatureFlag
    flag = FeatureFlag(
        key="toggle_test",
        name="Toggle Test",
        enabled=True,
        created_by="system", updated_by="system",
    )
    session.add(flag)
    await session.flush()
    flag.enabled = False
    await session.flush()
    await session.refresh(flag)
    assert flag.enabled is False


@pytest.mark.asyncio
async def test_create_system_error(session):
    from app.modules.error_tracking.service import SystemError
    err = SystemError(
        level="ERROR",
        module="test_module",
        message="Test error occurred",
        resolved=False,
        created_by="system", updated_by="system",
    )
    session.add(err)
    await session.flush()
    await session.refresh(err)
    assert err.id is not None
    assert err.resolved is False


@pytest.mark.asyncio
async def test_resolve_system_error(session):
    from app.modules.error_tracking.service import SystemError
    err = SystemError(
        level="WARNING",
        module="scheduler",
        message="Scheduler warning",
        resolved=False,
        created_by="system", updated_by="system",
    )
    session.add(err)
    await session.flush()
    err.resolved = True
    err.resolved_by = "admin"
    await session.flush()
    await session.refresh(err)
    assert err.resolved is True
    assert err.resolved_by == "admin"
