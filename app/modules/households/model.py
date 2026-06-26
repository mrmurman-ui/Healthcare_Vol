from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import UUIDBase


class Household(UUIDBase):
    __tablename__ = "households"

    household_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    address: Mapped[str | None] = mapped_column(String(500))
    village: Mapped[str | None] = mapped_column(String(100))
    community: Mapped[str | None] = mapped_column(String(100))
    subdistrict: Mapped[str | None] = mapped_column(String(100))
    district: Mapped[str | None] = mapped_column(String(100))
    province: Mapped[str | None] = mapped_column(String(100))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    head_of_household: Mapped[str | None] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(20))
    income_group: Mapped[str | None] = mapped_column(String(20))
    housing_type: Mapped[str | None] = mapped_column(String(20))
