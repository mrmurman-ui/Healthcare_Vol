from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.volunteers.model import Volunteer
from app.modules.volunteers.repository import VolunteerRepository
from app.modules.volunteers.schema import VolunteerCreate, VolunteerUpdate


class VolunteerService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = VolunteerRepository(session)

    async def create(self, data: VolunteerCreate, actor: str = "system") -> Volunteer:
        vol = Volunteer(**data.model_dump(), created_by=actor, updated_by=actor)
        return await self.repo.create(vol)

    async def update(self, volunteer: Volunteer, data: VolunteerUpdate, actor: str = "system") -> Volunteer:
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(volunteer, field, value)
        volunteer.updated_by = actor
        return await self.repo.update(volunteer)

    async def search(self, query: str = "", province: str = "") -> list[Volunteer]:
        return await self.repo.search(query, province)

    async def get_stats(self) -> dict:
        return await self.repo.count_by_status()
