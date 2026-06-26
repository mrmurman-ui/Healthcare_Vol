import uuid

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import UUIDBase


class EarlyWarning(UUIDBase):
    __tablename__ = "early_warnings"

    citizen_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("citizens.id", ondelete="CASCADE"), nullable=True, index=True
    )
    alert_type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="low")  # low/medium/high/critical
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="open")  # open/acknowledged/resolved
    resolved_by: Mapped[str | None] = mapped_column(String(200))
    is_deleted: Mapped[bool] = mapped_column(default=False)


class CVIScore(UUIDBase):
    __tablename__ = "cvi_scores"

    citizen_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("citizens.id", ondelete="CASCADE"),
        unique=True, nullable=False, index=True
    )
    score: Mapped[float] = mapped_column(Float, default=0.0)
    category: Mapped[str] = mapped_column(String(20), default="low")
    age_score: Mapped[float] = mapped_column(Float, default=0.0)
    social_score: Mapped[float] = mapped_column(Float, default=0.0)
    health_score: Mapped[float] = mapped_column(Float, default=0.0)
    environment_score: Mapped[float] = mapped_column(Float, default=0.0)
    last_calculated: Mapped[str | None] = mapped_column(String(20))
