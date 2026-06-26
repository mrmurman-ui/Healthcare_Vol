"""Integration tests — HouseholdService and CitizenService."""
import pytest
import pytest_asyncio

from app.modules.citizens.service import CitizenCreate, CitizenService
from app.modules.households.service import HouseholdCreate, HouseholdService
from app.shared.enums import Gender, HousingType, IncomeGroup


@pytest_asyncio.fixture
async def hh_service(session):
    return HouseholdService(session)


@pytest_asyncio.fixture
async def cit_service(session):
    return CitizenService(session)


async def _make_household(svc, code="HH001"):
    return await svc.create(
        HouseholdCreate(
            household_code=code,
            head_of_household="สมชาย ใจดี",
            village="หมู่ 1",
            district="เมือง",
            province="เชียงใหม่",
            latitude=18.788,
            longitude=98.985,
            income_group=IncomeGroup.LOW,
            housing_type=HousingType.OWN,
        )
    )


@pytest.mark.asyncio
async def test_create_household(hh_service):
    hh = await _make_household(hh_service, "HH001")
    assert hh.id is not None
    assert hh.household_code == "HH001"


@pytest.mark.asyncio
async def test_search_household(hh_service):
    await _make_household(hh_service, "HH002")
    results = await hh_service.search("HH002")
    assert any(h.household_code == "HH002" for h in results)


@pytest.mark.asyncio
async def test_household_with_gps(hh_service):
    await _make_household(hh_service, "HH003")
    mapped = await hh_service.get_mapped()
    assert len(mapped) >= 1


@pytest.mark.asyncio
async def test_create_citizen(cit_service):
    from datetime import date
    cit = await cit_service.create(
        CitizenCreate(
            full_name="สมหญิง รักดี",
            gender=Gender.FEMALE,
            date_of_birth=date(1950, 5, 10),
            is_elderly=True,
        )
    )
    assert cit.id is not None
    assert cit.is_elderly is True


@pytest.mark.asyncio
async def test_citizen_flag_stats(cit_service):
    from datetime import date
    await cit_service.create(
        CitizenCreate(full_name="พิการ ทดสอบ", is_disabled=True)
    )
    stats = await cit_service.get_flag_stats()
    assert "disabled" in stats
    assert stats["disabled"] >= 1
    assert "total" in stats
