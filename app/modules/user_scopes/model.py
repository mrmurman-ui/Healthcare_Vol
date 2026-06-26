"""User Scopes — area-based data access control."""
from __future__ import annotations

import uuid
from datetime import datetime, UTC

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import UUIDBase


class UserScope(UUIDBase):
    __tablename__ = "user_scopes"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    province_code: Mapped[str | None] = mapped_column(String(100))
    district_code: Mapped[str | None] = mapped_column(String(100))
    subdistrict_code: Mapped[str | None] = mapped_column(String(100))
    village_code: Mapped[str | None] = mapped_column(String(100))
    assigned_by: Mapped[str | None] = mapped_column(String(200))
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True),
                                                          default=lambda: datetime.now(UTC))
    is_deleted: Mapped[bool] = mapped_column(default=False)

    @property
    def scope_level(self) -> str:
        if self.village_code:
            return "village"
        if self.subdistrict_code:
            return "subdistrict"
        if self.district_code:
            return "district"
        if self.province_code:
            return "province"
        return "national"

    def can_access(self, province: str | None = None, district: str | None = None,
                   subdistrict: str | None = None, village: str | None = None) -> bool:
        """Check if a record falls within this scope."""
        if self.scope_level == "national":
            return True
        if self.province_code and province and self.province_code != province:
            return False
        if self.district_code and district and self.district_code != district:
            return False
        if self.subdistrict_code and subdistrict and self.subdistrict_code != subdistrict:
            return False
        if self.village_code and village and self.village_code != village:
            return False
        return True
