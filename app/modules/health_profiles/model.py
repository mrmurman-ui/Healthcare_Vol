import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import UUIDBase


class HealthProfile(UUIDBase):
    __tablename__ = "health_profiles"

    citizen_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("citizens.id", ondelete="CASCADE"),
        unique=True, nullable=False, index=True
    )
    blood_type: Mapped[str | None] = mapped_column(String(5))
    allergies: Mapped[str | None] = mapped_column(Text)
    chronic_conditions: Mapped[str | None] = mapped_column(Text)  # JSON list as text
    medication_notes: Mapped[str | None] = mapped_column(Text)
    primary_caregiver: Mapped[str | None] = mapped_column(String(200))
    caregiver_phone: Mapped[str | None] = mapped_column(String(20))
    # Conditions (checkbox-based, no diagnosis)
    has_diabetes: Mapped[bool] = mapped_column(default=False)
    has_hypertension: Mapped[bool] = mapped_column(default=False)
    has_dyslipidemia: Mapped[bool] = mapped_column(default=False)
    has_heart_disease: Mapped[bool] = mapped_column(default=False)
    has_stroke: Mapped[bool] = mapped_column(default=False)
    has_cancer: Mapped[bool] = mapped_column(default=False)
    has_kidney_disease: Mapped[bool] = mapped_column(default=False)
    has_lung_disease: Mapped[bool] = mapped_column(default=False)
    other_conditions: Mapped[str | None] = mapped_column(String(500))
    # Functional status
    walks_independently: Mapped[bool] = mapped_column(default=True)
    uses_cane: Mapped[bool] = mapped_column(default=False)
    uses_walker: Mapped[bool] = mapped_column(default=False)
    uses_wheelchair: Mapped[bool] = mapped_column(default=False)
    is_homebound: Mapped[bool] = mapped_column(default=False)
    is_bedridden_profile: Mapped[bool] = mapped_column(default=False)
    # Social health
    lives_alone_profile: Mapped[bool] = mapped_column(default=False)
    has_caregiver: Mapped[bool] = mapped_column(default=False)
    has_income_problems: Mapped[bool] = mapped_column(default=False)
    has_food_insecurity: Mapped[bool] = mapped_column(default=False)
    has_social_isolation: Mapped[bool] = mapped_column(default=False)
    has_healthcare_access_issues: Mapped[bool] = mapped_column(default=False)
    # Home environment
    unsafe_bathroom: Mapped[bool] = mapped_column(default=False)
    slippery_floor: Mapped[bool] = mapped_column(default=False)
    poor_lighting: Mapped[bool] = mapped_column(default=False)
    unsafe_stairs: Mapped[bool] = mapped_column(default=False)
    electrical_hazards: Mapped[bool] = mapped_column(default=False)
    structural_damage: Mapped[bool] = mapped_column(default=False)
    # Service needs
    needs_home_visit: Mapped[bool] = mapped_column(default=False)
    needs_transportation: Mapped[bool] = mapped_column(default=False)
    needs_welfare_assistance: Mapped[bool] = mapped_column(default=False)
    needs_home_modification: Mapped[bool] = mapped_column(default=False)
    needs_equipment_support: Mapped[bool] = mapped_column(default=False)
    needs_social_support: Mapped[bool] = mapped_column(default=False)
    is_deleted: Mapped[bool] = mapped_column(default=False)
