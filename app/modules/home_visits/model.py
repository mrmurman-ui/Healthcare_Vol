import uuid

from sqlalchemy import Date, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import UUIDBase
from app.shared.enums import VisitType


class HomeVisit(UUIDBase):
    __tablename__ = "home_visits"

    citizen_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("citizens.id", ondelete="SET NULL"), index=True, nullable=True
    )
    volunteer_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("volunteers.id", ondelete="SET NULL"), index=True, nullable=True
    )
    visit_date: Mapped[str] = mapped_column(Date, nullable=False)
    visit_type: Mapped[str] = mapped_column(String(20), default=VisitType.ROUTINE)
    observation: Mapped[str | None] = mapped_column(Text)
    recommendation: Mapped[str | None] = mapped_column(Text)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    photo_urls: Mapped[str | None] = mapped_column(Text)
