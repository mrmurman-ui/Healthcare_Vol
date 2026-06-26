import uuid

from sqlalchemy import Boolean, Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import UUIDBase


class Citizen(UUIDBase):
    __tablename__ = "citizens"

    household_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("households.id", ondelete="SET NULL"), index=True, nullable=True
    )
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    gender: Mapped[str | None] = mapped_column(String(10))
    date_of_birth: Mapped[str | None] = mapped_column(Date)
    occupation: Mapped[str | None] = mapped_column(String(100))
    education: Mapped[str | None] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(20))
    is_elderly: Mapped[bool] = mapped_column(Boolean, default=False)
    is_disabled: Mapped[bool] = mapped_column(Boolean, default=False)
    is_bedridden: Mapped[bool] = mapped_column(Boolean, default=False)
    is_pregnant: Mapped[bool] = mapped_column(Boolean, default=False)
    is_living_alone: Mapped[bool] = mapped_column(Boolean, default=False)
