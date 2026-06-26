import uuid

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import UUIDBase
from app.shared.enums import ReferralStatus, ReferralTarget


class Referral(UUIDBase):
    __tablename__ = "referrals"

    citizen_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("citizens.id", ondelete="SET NULL"), index=True, nullable=True
    )
    volunteer_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("volunteers.id", ondelete="SET NULL"), index=True, nullable=True
    )
    referral_date: Mapped[str] = mapped_column(Date, nullable=False)
    target: Mapped[str] = mapped_column(String(30), nullable=False)
    target_name: Mapped[str | None] = mapped_column(String(200))
    reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default=ReferralStatus.PENDING)
    outcome: Mapped[str | None] = mapped_column(Text)
    followup_date: Mapped[str | None] = mapped_column(Date)
    followup_notes: Mapped[str | None] = mapped_column(Text)
