import uuid
from datetime import date, datetime

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.referrals.model import Referral
from app.shared.enums import ReferralStatus, ReferralTarget
from app.shared.repository import BaseRepository


# ── Schemas ──────────────────────────────────────────────────────────────────

class ReferralCreate(BaseModel):
    citizen_id: uuid.UUID | None = None
    volunteer_id: uuid.UUID | None = None
    referral_date: date
    target: ReferralTarget
    target_name: str | None = None
    reason: str | None = None
    status: ReferralStatus = ReferralStatus.PENDING
    outcome: str | None = None
    followup_date: date | None = None
    followup_notes: str | None = None


class ReferralUpdate(BaseModel):
    status: ReferralStatus | None = None
    outcome: str | None = None
    followup_date: date | None = None
    followup_notes: str | None = None


class ReferralRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    citizen_id: uuid.UUID | None
    volunteer_id: uuid.UUID | None
    referral_date: date
    target: ReferralTarget
    target_name: str | None
    reason: str | None
    status: ReferralStatus
    outcome: str | None
    followup_date: date | None
    created_at: datetime


# ── Repository ────────────────────────────────────────────────────────────────

class ReferralRepository(BaseRepository[Referral]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Referral, session)

    async def by_status(self, status: ReferralStatus) -> list[Referral]:
        result = await self.session.execute(
            select(Referral).where(Referral.status == status)
        )
        return list(result.scalars().all())

    async def status_counts(self) -> dict:
        result = await self.session.execute(
            select(Referral.status, func.count()).group_by(Referral.status)
        )
        return {row[0]: row[1] for row in result.all()}


# ── Service ───────────────────────────────────────────────────────────────────

class ReferralService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = ReferralRepository(session)

    async def create(self, data: ReferralCreate, actor: str = "system") -> Referral:
        ref = Referral(**data.model_dump(), created_by=actor, updated_by=actor)
        return await self.repo.create(ref)

    async def update_status(self, referral: Referral, data: ReferralUpdate, actor: str = "system") -> Referral:
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(referral, field, value)
        referral.updated_by = actor
        return await self.repo.update(referral)

    async def get_stats(self) -> dict:
        return await self.repo.status_counts()
