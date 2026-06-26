"""Integration tests — VolunteerService."""
import pytest
import pytest_asyncio

from app.modules.volunteers.schema import VolunteerCreate, VolunteerUpdate
from app.modules.volunteers.service import VolunteerService
from app.shared.enums import VolunteerStatus


@pytest_asyncio.fixture
async def vol_service(session):
    return VolunteerService(session)


async def _make_volunteer(svc, suffix="01"):
    return await svc.create(
        VolunteerCreate(
            volunteer_code=f"VOL{suffix}",
            full_name=f"Test Volunteer {suffix}",
            phone="0812345678",
            province="เชียงใหม่",
            district="เมือง",
            status=VolunteerStatus.ACTIVE,
        )
    )


@pytest.mark.asyncio
async def test_create_volunteer(vol_service):
    vol = await _make_volunteer(vol_service, "01")
    assert vol.id is not None
    assert vol.volunteer_code == "VOL01"
    assert vol.status == VolunteerStatus.ACTIVE


@pytest.mark.asyncio
async def test_search_by_name(vol_service):
    await _make_volunteer(vol_service, "02")
    results = await vol_service.search("Volunteer 02")
    assert any(v.volunteer_code == "VOL02" for v in results)


@pytest.mark.asyncio
async def test_search_by_province(vol_service):
    await _make_volunteer(vol_service, "03")
    results = await vol_service.search(province="เชียงใหม่")
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_update_volunteer(vol_service):
    vol = await _make_volunteer(vol_service, "04")
    updated = await vol_service.update(vol, VolunteerUpdate(status=VolunteerStatus.INACTIVE))
    assert updated.status == VolunteerStatus.INACTIVE


@pytest.mark.asyncio
async def test_get_stats_returns_dict(vol_service):
    await _make_volunteer(vol_service, "05")
    stats = await vol_service.get_stats()
    assert isinstance(stats, dict)
    assert VolunteerStatus.ACTIVE in stats or "active" in str(stats)
