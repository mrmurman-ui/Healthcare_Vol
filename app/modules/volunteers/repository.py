from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.volunteers.model import Volunteer
from app.shared.enums import VolunteerStatus
from app.shared.repository import BaseRepository


class VolunteerRepository(BaseRepository[Volunteer]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Volunteer, session)

    async def search(self, query: str = "", province: str = "") -> list[Volunteer]:
        stmt = select(Volunteer)
        if query:
            stmt = stmt.where(
                Volunteer.full_name.ilike(f"%{query}%")
                | Volunteer.volunteer_code.ilike(f"%{query}%")
            )
        if province:
            stmt = stmt.where(Volunteer.province == province)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_status(self) -> dict[str, int]:
        from sqlalchemy import func
        result = await self.session.execute(
            select(Volunteer.status, func.count()).group_by(Volunteer.status)
        )
        return {row[0]: row[1] for row in result.all()}
