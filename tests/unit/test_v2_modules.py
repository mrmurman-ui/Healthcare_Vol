"""Unit tests for V2 modules."""
import pytest
from unittest.mock import MagicMock, patch


# ── Task tests ────────────────────────────────────────────────────────────────

def test_task_priorities():
    from app.modules.tasks.service import PRIORITIES
    assert "critical" in PRIORITIES
    assert "high" in PRIORITIES
    assert "medium" in PRIORITIES
    assert "low" in PRIORITIES


def test_task_statuses():
    from app.modules.tasks.service import STATUSES
    assert "new" in STATUSES
    assert "completed" in STATUSES
    assert "overdue" in STATUSES


def test_task_types():
    from app.modules.tasks.service import TASK_TYPES
    assert "home_visit" in TASK_TYPES
    assert "referral_followup" in TASK_TYPES


# ── Followup tests ────────────────────────────────────────────────────────────

def test_followup_types():
    from app.modules.followups.service import FOLLOWUP_TYPES
    assert "citizen_not_visited" in FOLLOWUP_TYPES
    assert "referral_unresolved" in FOLLOWUP_TYPES


# ── Announcement tests ────────────────────────────────────────────────────────

def test_announcement_types():
    from app.modules.announcements.service import ANNOUNCEMENT_TYPES
    assert "emergency_alert" in ANNOUNCEMENT_TYPES
    assert "health_campaign" in ANNOUNCEMENT_TYPES
    assert "volunteer_notice" in ANNOUNCEMENT_TYPES


# ── Community project tests ───────────────────────────────────────────────────

def test_project_types():
    from app.modules.community_projects.service import PROJECT_TYPES
    assert "elderly_club" in PROJECT_TYPES
    assert "exercise_program" in PROJECT_TYPES


def test_project_statuses():
    from app.modules.community_projects.service import PROJECT_STATUSES
    assert "planning" in PROJECT_STATUSES
    assert "active" in PROJECT_STATUSES
    assert "completed" in PROJECT_STATUSES


# ── Notification tests ────────────────────────────────────────────────────────

def test_notification_types():
    from app.modules.notifications.service import NOTIF_TYPES
    assert "new_task" in NOTIF_TYPES
    assert "overdue_task" in NOTIF_TYPES
    assert "new_announcement" in NOTIF_TYPES


# ── AI Assistant tests ────────────────────────────────────────────────────────

def test_ai_summary_types():
    from app.modules.ai_assistant.service import SUMMARY_TYPES
    assert len(SUMMARY_TYPES) >= 5
    assert any("Weekly" in s for s in SUMMARY_TYPES)
    assert any("Executive" in s for s in SUMMARY_TYPES)


def test_ai_system_prompt_no_diagnosis():
    from app.modules.ai_assistant.service import SYSTEM_PROMPT
    assert "NOT diagnose" in SYSTEM_PROMPT
    assert "NOT" in SYSTEM_PROMPT


def test_ai_providers():
    from app.modules.ai_assistant.service import PROVIDERS
    assert any("Claude" in p for p in PROVIDERS)
    assert any("OpenAI" in p for p in PROVIDERS)
    assert any("Gemini" in p for p in PROVIDERS)


def test_ai_call_bad_key_returns_error():
    from app.modules.ai_assistant.service import call_ai
    result = call_ai("test prompt", "Claude (Anthropic)", "bad-key")
    assert "Error" in result or "error" in result.lower()


# ── Localization V2 tests ─────────────────────────────────────────────────────

def test_v2_thai_translations():
    from unittest.mock import patch
    import streamlit as st
    with patch.object(st, "session_state", {"locale": "th"}):
        from app.modules.localization.service import t
        assert t("nav_tasks") == "การจัดการงาน"
        assert t("nav_analytics") == "วิเคราะห์ข้อมูล"
        assert t("nav_ai_assistant") == "ผู้ช่วย AI"


def test_v2_english_translations():
    from unittest.mock import patch
    import streamlit as st
    with patch.object(st, "session_state", {"locale": "en"}):
        from app.modules.localization.service import t
        assert t("nav_tasks") == "Tasks"
        assert t("nav_analytics") == "Analytics"
        assert t("nav_ai_assistant") == "AI Assistant"
