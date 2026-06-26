"""Health Campaigns model."""
from __future__ import annotations
from sqlalchemy import Boolean, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.base_model import UUIDBase


class Campaign(UUIDBase):
    __tablename__ = "health_campaigns"

    campaign_code: Mapped[str]         = mapped_column(String(50), unique=True, index=True)
    campaign_name: Mapped[str]         = mapped_column(String(300), nullable=False)
    campaign_type: Mapped[str | None]  = mapped_column(String(50), default="health_screening")
    description:   Mapped[str | None]  = mapped_column(Text)
    target_group:  Mapped[str | None]  = mapped_column(String(100))   # elderly, all, women, etc.
    start_date:    Mapped[str | None]  = mapped_column(String(20))
    end_date:      Mapped[str | None]  = mapped_column(String(20))
    province:      Mapped[str | None]  = mapped_column(String(100))
    district:      Mapped[str | None]  = mapped_column(String(100))
    venue:         Mapped[str | None]  = mapped_column(String(300))
    budget:        Mapped[float | None]= mapped_column(Float)
    target_count:  Mapped[int | None]  = mapped_column(Integer)
    actual_count:  Mapped[int | None]  = mapped_column(Integer)
    status:        Mapped[str | None]  = mapped_column(String(20), default="planning", index=True)
    organizer:     Mapped[str | None]  = mapped_column(String(200))
    notes:         Mapped[str | None]  = mapped_column(Text)
    is_deleted:    Mapped[bool]        = mapped_column(Boolean, default=False)
    created_by:    Mapped[str | None]  = mapped_column(String(100))
    updated_by:    Mapped[str | None]  = mapped_column(String(100))
