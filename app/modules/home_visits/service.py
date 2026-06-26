import uuid
from datetime import date, datetime

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.home_visits.model import HomeVisit
from app.shared.enums import VisitType
from app.shared.repository import BaseRepository


# ── Schemas ──────────────────────────────────────────────────────────────────

class HomeVisitCreate(BaseModel):
    citizen_id: uuid.UUID | None = None
    volunteer_id: uuid.UUID | None = None
    visit_date: date
    visit_type: VisitType = VisitType.ROUTINE
    observation: str | None = None
    recommendation: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    photo_urls: str | None = None


class HomeVisitRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    citizen_id: uuid.UUID | None
    volunteer_id: uuid.UUID | None
    visit_date: date
    visit_type: VisitType
    observation: str | None
    recommendation: str | None
    latitude: float | None
    longitude: float | None
    created_at: datetime


# ── Repository ────────────────────────────────────────────────────────────────

class HomeVisitRepository(BaseRepository[HomeVisit]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(HomeVisit, session)

    async def by_citizen(self, citizen_id: uuid.UUID) -> list[HomeVisit]:
        result = await self.session.execute(
            select(HomeVisit)
            .where(HomeVisit.citizen_id == citizen_id)
            .order_by(HomeVisit.visit_date.desc())
        )
        return list(result.scalars().all())

    async def recent(self, limit: int = 20) -> list[HomeVisit]:
        result = await self.session.execute(
            select(HomeVisit).order_by(HomeVisit.visit_date.desc()).limit(limit)
        )
        return list(result.scalars().all())


# ── Service ───────────────────────────────────────────────────────────────────

class HomeVisitService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = HomeVisitRepository(session)

    async def create(self, data: HomeVisitCreate, actor: str = "system") -> HomeVisit:
        visit = HomeVisit(**data.model_dump(), created_by=actor, updated_by=actor)
        return await self.repo.create(visit)

    async def get_by_citizen(self, citizen_id: uuid.UUID) -> list[HomeVisit]:
        return await self.repo.by_citizen(citizen_id)

    async def get_recent(self, limit: int = 20) -> list[HomeVisit]:
        return await self.repo.recent(limit)
