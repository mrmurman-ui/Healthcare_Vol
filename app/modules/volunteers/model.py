from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import UUIDBase
from app.shared.enums import VolunteerStatus


class Volunteer(UUIDBase):
    __tablename__ = "volunteers"

    volunteer_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(255))
    province: Mapped[str | None] = mapped_column(String(100))
    district: Mapped[str | None] = mapped_column(String(100))
    subdistrict: Mapped[str | None] = mapped_column(String(100))
    village: Mapped[str | None] = mapped_column(String(100))
    position: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default=VolunteerStatus.ACTIVE)
    photo_url: Mapped[str | None] = mapped_column(String(500))
