"""Integration tests — ReferralService and HomeVisitService."""
from datetime import date

import pytest
import pytest_asyncio

from app.modules.home_visits.service import HomeVisitCreate, HomeVisitService
from app.modules.referrals.service import ReferralCreate, ReferralService, ReferralUpdate
from app.shared.enums import ReferralStatus, ReferralTarget, VisitType


@pytest_asyncio.fixture
async def ref_service(session):
    return ReferralService(session)


@pytest_asyncio.fixture
async def vis_service(session):
    return HomeVisitService(session)


@pytest.mark.asyncio
async def test_create_referral(ref_service):
    ref = await ref_service.create(
        ReferralCreate(
            referral_date=date.today(),
            target=ReferralTarget.HOSPITAL,
            target_name="โรงพยาบาลเชียงใหม่",
            reason="ส่งต่อตรวจเพิ่มเติม",
        )
    )
    assert ref.id is not None
    assert ref.status == ReferralStatus.PENDING
    assert ref.target == ReferralTarget.HOSPITAL


@pytest.mark.asyncio
async def test_update_referral_status(ref_service):
    ref = await ref_service.create(
        ReferralCreate(referral_date=date.today(), target=ReferralTarget.NGO)
    )
    updated = await ref_service.update_status(
        ref, ReferralUpdate(status=ReferralStatus.COMPLETED, outcome="ได้รับการช่วยเหลือแล้ว")
    )
    assert updated.status == ReferralStatus.COMPLETED
    assert updated.outcome == "ได้รับการช่วยเหลือแล้ว"


@pytest.mark.asyncio
async def test_referral_stats(ref_service):
    await ref_service.create(
        ReferralCreate(referral_date=date.today(), target=ReferralTarget.HEALTH_CENTER)
    )
    stats = await ref_service.get_stats()
    assert isinstance(stats, dict)
    assert len(stats) >= 1


@pytest.mark.asyncio
async def test_create_home_visit(vis_service):
    visit = await vis_service.create(
        HomeVisitCreate(
            visit_date=date.today(),
            visit_type=VisitType.ROUTINE,
            observation="ผู้ป่วยมีสุขภาพแข็งแรงดี",
            recommendation="ให้ดูแลสุขภาพต่อเนื่อง",
            latitude=18.788,
            longitude=98.985,
        )
    )
    assert visit.id is not None
    assert visit.visit_type == VisitType.ROUTINE


@pytest.mark.asyncio
async def test_get_recent_visits(vis_service):
    for _ in range(3):
        await vis_service.create(
            HomeVisitCreate(visit_date=date.today(), visit_type=VisitType.FOLLOW_UP)
        )
    recent = await vis_service.get_recent(10)
    assert len(recent) >= 3


@pytest.mark.asyncio
async def test_audit_log_creation(session):
    from app.modules.audit.service import AuditLog, AuditService
    from sqlalchemy import select

    svc = AuditService(session)
    await svc.log(
        actor="admin@test.com",
        action="CREATE",
        resource_type="volunteer",
        resource_id="vol-123",
        detail="Created volunteer VOL001",
    )
    await session.flush()
    result = await session.execute(select(AuditLog).where(AuditLog.actor == "admin@test.com"))
    logs = result.scalars().all()
    assert len(logs) == 1
    assert logs[0].action == "CREATE"
