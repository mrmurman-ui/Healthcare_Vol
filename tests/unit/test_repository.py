"""Unit tests — BaseRepository CRUD."""
import uuid

import pytest
import pytest_asyncio

from app.modules.volunteers.model import Volunteer
from app.modules.volunteers.repository import VolunteerRepository
from app.shared.enums import VolunteerStatus


@pytest_asyncio.fixture
async def repo(session):
    return VolunteerRepository(session)


def _vol(suffix="99"):
    return Volunteer(
        id=uuid.uuid4(),
        volunteer_code=f"REPO{suffix}",
        full_name=f"Repo Test {suffix}",
        status=VolunteerStatus.ACTIVE,
    )


@pytest.mark.asyncio
async def test_create_and_get(repo):
    vol = await repo.create(_vol("01"))
    fetched = await repo.get(vol.id)
    assert fetched is not None
    assert fetched.volunteer_code == "REPO01"


@pytest.mark.asyncio
async def test_list(repo):
    await repo.create(_vol("02"))
    await repo.create(_vol("03"))
    items = await repo.list(limit=50)
    codes = [v.volunteer_code for v in items]
    assert "REPO02" in codes
    assert "REPO03" in codes


@pytest.mark.asyncio
async def test_get_nonexistent_returns_none(repo):
    result = await repo.get(uuid.uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_delete(repo):
    vol = await repo.create(_vol("04"))
    await repo.delete(vol)
    assert await repo.get(vol.id) is None
