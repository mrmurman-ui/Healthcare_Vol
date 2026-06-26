"""Community Projects model — matches 0002_v2_schema migration."""
from __future__ import annotations
import uuid
from sqlalchemy import Boolean, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.base_model import UUIDBase


class CommunityProject(UUIDBase):
    __tablename__ = "community_projects"

    project_code: Mapped[str]          = mapped_column(String(50),  unique=True, nullable=False, index=True)
    project_name: Mapped[str]          = mapped_column(String(300), nullable=False)
    project_type: Mapped[str | None]   = mapped_column(String(50),  default="other")
    description:  Mapped[str | None]   = mapped_column(Text)
    start_date:   Mapped[str | None]   = mapped_column(String(20))
    end_date:     Mapped[str | None]   = mapped_column(String(20))
    budget:       Mapped[float | None] = mapped_column(Float)
    status:       Mapped[str | None]   = mapped_column(String(20),  default="planning", index=True)
    owner:        Mapped[str | None]   = mapped_column(String(200))
    province:     Mapped[str | None]   = mapped_column(String(100))
    district:     Mapped[str | None]   = mapped_column(String(100))
    latitude:     Mapped[float | None] = mapped_column(Float)
    longitude:    Mapped[float | None] = mapped_column(Float)
    is_deleted:   Mapped[bool]         = mapped_column(Boolean, default=False)
    created_by:   Mapped[str | None]   = mapped_column(String(100))
    updated_by:   Mapped[str | None]   = mapped_column(String(100))
