import uuid
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.households.model import Household
from app.shared.enums import HousingType, IncomeGroup
from app.shared.repository import BaseRepository


# ── Schemas ──────────────────────────────────────────────────────────────────

class HouseholdCreate(BaseModel):
    household_code: str
    address: str | None = None
    village: str | None = None
    community: str | None = None
    subdistrict: str | None = None
    district: str | None = None
    province: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    head_of_household: str | None = None
    phone: str | None = None
    income_group: IncomeGroup | None = None
    housing_type: HousingType | None = None


class HouseholdRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    household_code: str
    address: str | None
    village: str | None
    community: str | None
    district: str | None
    province: str | None
    latitude: float | None
    longitude: float | None
    head_of_household: str | None
    phone: str | None
    income_group: IncomeGroup | None
    housing_type: HousingType | None
    created_at: datetime


# ── Repository ────────────────────────────────────────────────────────────────

class HouseholdRepository(BaseRepository[Household]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Household, session)

    async def search(self, query: str = "") -> list[Household]:
        stmt = select(Household)
        if query:
            stmt = stmt.where(
                Household.household_code.ilike(f"%{query}%")
                | Household.head_of_household.ilike(f"%{query}%")
            )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def with_gps(self) -> list[Household]:
        result = await self.session.execute(
            select(Household).where(
                Household.latitude.isnot(None),
                Household.longitude.isnot(None),
            )
        )
        return list(result.scalars().all())


# ── Service ───────────────────────────────────────────────────────────────────

class HouseholdService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = HouseholdRepository(session)

    async def create(self, data: HouseholdCreate, actor: str = "system") -> Household:
        hh = Household(**data.model_dump(), created_by=actor, updated_by=actor)
        return await self.repo.create(hh)

    async def search(self, query: str = "") -> list[Household]:
        return await self.repo.search(query)

    async def get_mapped(self) -> list[Household]:
        return await self.repo.with_gps()
