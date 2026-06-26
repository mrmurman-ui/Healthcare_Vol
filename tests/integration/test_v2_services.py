"""Integration tests for V2 modules — Task, Followup, Notification, Announcement, Project."""
import uuid
from datetime import date

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.modules.tasks.model import Task
from app.modules.followups.model import Followup
from app.modules.notifications.service import Notification
from app.modules.announcements.service import Announcement
from app.modules.community_projects.service import CommunityProject


# ── Task integration ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_task(session):
    task = Task(
        task_code="TASK00001",
        title="Visit elderly patient",
        task_type="home_visit",
        priority="high",
        status="new",
        created_by="test",
        updated_by="test",
    )
    session.add(task)
    await session.flush()
    await session.refresh(task)
    assert task.id is not None
    assert task.status == "new"
    assert task.priority == "high"


@pytest.mark.asyncio
async def test_task_soft_delete(session):
    task = Task(
        task_code="TASK00002",
        title="Test soft delete",
        task_type="community_survey",
        priority="low",
        status="new",
        is_deleted=False,
        created_by="test", updated_by="test",
    )
    session.add(task)
    await session.flush()
    task.is_deleted = True
    await session.flush()

    result = await session.execute(
        select(Task).where(Task.task_code == "TASK00002", Task.is_deleted == False)
    )
    assert result.scalar_one_or_none() is None


# ── Followup integration ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_followup(session):
    fu = Followup(
        followup_type="citizen_not_visited",
        followup_date=str(date.today()),
        status="pending",
        rule_triggered="No visit in 90 days",
        created_by="system", updated_by="system",
    )
    session.add(fu)
    await session.flush()
    await session.refresh(fu)
    assert fu.id is not None
    assert fu.followup_type == "citizen_not_visited"
    assert fu.status == "pending"


# ── Notification integration ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_notification(session):
    notif = Notification(
        type="new_task",
        title="New task assigned",
        message="You have a new home visit task.",
        is_read=False,
        created_by="system", updated_by="system",
    )
    session.add(notif)
    await session.flush()
    await session.refresh(notif)
    assert notif.id is not None
    assert notif.is_read is False


@pytest.mark.asyncio
async def test_mark_notification_read(session):
    notif = Notification(
        type="overdue_task",
        title="Overdue!",
        is_read=False,
        created_by="system", updated_by="system",
    )
    session.add(notif)
    await session.flush()
    notif.is_read = True
    await session.flush()
    await session.refresh(notif)
    assert notif.is_read is True


# ── Announcement integration ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_announcement(session):
    ann = Announcement(
        title="Health Campaign 2026",
        content="Please get vaccinated.",
        announcement_type="health_campaign",
        start_date=str(date.today()),
        is_active=True,
        created_by="admin", updated_by="admin",
    )
    session.add(ann)
    await session.flush()
    await session.refresh(ann)
    assert ann.id is not None
    assert ann.announcement_type == "health_campaign"
    assert ann.is_active is True


# ── Community Project integration ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_project(session):
    proj = CommunityProject(
        project_code="PROJ0001",
        project_name="Elderly Club Chiang Mai",
        project_type="elderly_club",
        status="planning",
        budget=50000.0,
        owner="admin@healthcare.com",
        created_by="admin", updated_by="admin",
    )
    session.add(proj)
    await session.flush()
    await session.refresh(proj)
    assert proj.id is not None
    assert proj.project_type == "elderly_club"
    assert proj.budget == 50000.0


@pytest.mark.asyncio
async def test_project_status_transition(session):
    proj = CommunityProject(
        project_code="PROJ0002",
        project_name="Exercise Program",
        project_type="exercise_program",
        status="planning",
        created_by="admin", updated_by="admin",
    )
    session.add(proj)
    await session.flush()
    proj.status = "active"
    await session.flush()
    await session.refresh(proj)
    assert proj.status == "active"
