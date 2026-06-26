import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import UUIDBase


class Followup(UUIDBase):
    __tablename__ = "followups"

    citizen_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("citizens.id", ondelete="SET NULL"), nullable=True, index=True
    )
    referral_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("referrals.id", ondelete="SET NULL"), nullable=True
    )
    followup_type: Mapped[str] = mapped_column(String(50), nullable=False)
    followup_date: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    assigned_to: Mapped[str | None] = mapped_column(String(200))
    notes: Mapped[str | None] = mapped_column(Text)
    rule_triggered: Mapped[str | None] = mapped_column(String(200))
