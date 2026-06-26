import uuid

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import UUIDBase

ASSESSMENT_TYPES = [
    "routine", "follow_up", "annual", "pre_referral", "post_referral",
]


class HealthAssessment(UUIDBase):
    __tablename__ = "health_assessments"

    citizen_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("citizens.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    volunteer_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("volunteers.id", ondelete="SET NULL"), nullable=True
    )
    assessment_date: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    assessment_type: Mapped[str] = mapped_column(String(50), default="routine")
    # Measurements
    height_cm: Mapped[float | None] = mapped_column(Float)
    weight_kg: Mapped[float | None] = mapped_column(Float)
    bmi: Mapped[float | None] = mapped_column(Float)
    waist_cm: Mapped[float | None] = mapped_column(Float)
    bp_systolic: Mapped[float | None] = mapped_column(Float)
    bp_diastolic: Mapped[float | None] = mapped_column(Float)
    pulse_rate: Mapped[float | None] = mapped_column(Float)
    temperature_c: Mapped[float | None] = mapped_column(Float)
    blood_sugar: Mapped[float | None] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text)
    is_deleted: Mapped[bool] = mapped_column(default=False)
