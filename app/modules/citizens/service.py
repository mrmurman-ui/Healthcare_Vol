import uuid
from datetime import date, datetime

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.citizens.model import Citizen
from app.shared.enums import Gender
from app.shared.repository import BaseRepository


# ── Schemas ──────────────────────────────────────────────────────────────────

class CitizenCreate(BaseModel):
    household_id: uuid.UUID | None = None
    full_name: str
    gender: Gender | None = None
    date_of_birth: date | None = None
    occupation: str | None = None
    education: str | None = None
    phone: str | None = None
    is_elderly: bool = False
    is_disabled: bool = False
    is_bedridden: bool = False
    is_pregnant: bool = False
    is_living_alone: bool = False


class CitizenRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    household_id: uuid.UUID | None
    full_name: str
    gender: Gender | None
    date_of_birth: date | None
    occupation: str | None
    education: str | None
    phone: str | None
    is_elderly: bool
    is_disabled: bool
    is_bedridden: bool
    is_pregnant: bool
    is_living_alone: bool
    created_at: datetime


# ── Repository ────────────────────────────────────────────────────────────────

class CitizenRepository(BaseRepository[Citizen]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Citizen, session)

    async def search(self, query: str = "") -> list[Citizen]:
        stmt = select(Citizen)
        if query:
            stmt = stmt.where(Citizen.full_name.ilike(f"%{query}%"))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def flag_counts(self) -> dict:
        result = await self.session.execute(
            select(
                func.sum(Citizen.is_elderly.cast(type_=None)).label("elderly"),
                func.sum(Citizen.is_disabled.cast(type_=None)).label("disabled"),
                func.sum(Citizen.is_bedridden.cast(type_=None)).label("bedridden"),
                func.sum(Citizen.is_pregnant.cast(type_=None)).label("pregnant"),
                func.sum(Citizen.is_living_alone.cast(type_=None)).label("alone"),
                func.count().label("total"),
            )
        )
        row = result.one()
        return {
            "elderly": int(row.elderly or 0),
            "disabled": int(row.disabled or 0),
            "bedridden": int(row.bedridden or 0),
            "pregnant": int(row.pregnant or 0),
            "living_alone": int(row.alone or 0),
            "total": int(row.total or 0),
        }


# ── Service ───────────────────────────────────────────────────────────────────

class CitizenService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = CitizenRepository(session)

    async def create(self, data: CitizenCreate, actor: str = "system") -> Citizen:
        citizen = Citizen(**data.model_dump(), created_by=actor, updated_by=actor)
        return await self.repo.create(citizen)

    async def search(self, query: str = "") -> list[Citizen]:
        return await self.repo.search(query)

    async def get_flag_stats(self) -> dict:
        return await self.repo.flag_counts()
