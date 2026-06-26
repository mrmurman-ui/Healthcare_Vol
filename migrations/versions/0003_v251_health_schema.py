"""V2.51 — health_profiles, health_assessments, early_warnings, cvi_scores

Revision ID: 0003
Revises: 0002
Create Date: 2025-01-03 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # health_profiles
    op.create_table(
        "health_profiles",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("citizen_id", sa.UUID(), sa.ForeignKey("citizens.id", ondelete="CASCADE"),
                  nullable=False, unique=True),
        sa.Column("blood_type", sa.String(5)),
        sa.Column("allergies", sa.Text()),
        sa.Column("chronic_conditions", sa.Text()),
        sa.Column("medication_notes", sa.Text()),
        sa.Column("primary_caregiver", sa.String(200)),
        sa.Column("caregiver_phone", sa.String(20)),
        sa.Column("other_conditions", sa.String(500)),
        # Conditions
        sa.Column("has_diabetes", sa.Boolean(), default=False),
        sa.Column("has_hypertension", sa.Boolean(), default=False),
        sa.Column("has_dyslipidemia", sa.Boolean(), default=False),
        sa.Column("has_heart_disease", sa.Boolean(), default=False),
        sa.Column("has_stroke", sa.Boolean(), default=False),
        sa.Column("has_cancer", sa.Boolean(), default=False),
        sa.Column("has_kidney_disease", sa.Boolean(), default=False),
        sa.Column("has_lung_disease", sa.Boolean(), default=False),
        # Functional
        sa.Column("walks_independently", sa.Boolean(), default=True),
        sa.Column("uses_cane", sa.Boolean(), default=False),
        sa.Column("uses_walker", sa.Boolean(), default=False),
        sa.Column("uses_wheelchair", sa.Boolean(), default=False),
        sa.Column("is_homebound", sa.Boolean(), default=False),
        sa.Column("is_bedridden_profile", sa.Boolean(), default=False),
        # Social
        sa.Column("lives_alone_profile", sa.Boolean(), default=False),
        sa.Column("has_caregiver", sa.Boolean(), default=False),
        sa.Column("has_income_problems", sa.Boolean(), default=False),
        sa.Column("has_food_insecurity", sa.Boolean(), default=False),
        sa.Column("has_social_isolation", sa.Boolean(), default=False),
        sa.Column("has_healthcare_access_issues", sa.Boolean(), default=False),
        # Home environment
        sa.Column("unsafe_bathroom", sa.Boolean(), default=False),
        sa.Column("slippery_floor", sa.Boolean(), default=False),
        sa.Column("poor_lighting", sa.Boolean(), default=False),
        sa.Column("unsafe_stairs", sa.Boolean(), default=False),
        sa.Column("electrical_hazards", sa.Boolean(), default=False),
        sa.Column("structural_damage", sa.Boolean(), default=False),
        # Service needs
        sa.Column("needs_home_visit", sa.Boolean(), default=False),
        sa.Column("needs_transportation", sa.Boolean(), default=False),
        sa.Column("needs_welfare_assistance", sa.Boolean(), default=False),
        sa.Column("needs_home_modification", sa.Boolean(), default=False),
        sa.Column("needs_equipment_support", sa.Boolean(), default=False),
        sa.Column("needs_social_support", sa.Boolean(), default=False),
        sa.Column("is_deleted", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
    )
    op.create_index("ix_health_profiles_citizen_id", "health_profiles", ["citizen_id"])

    # health_assessments
    op.create_table(
        "health_assessments",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("citizen_id", sa.UUID(), sa.ForeignKey("citizens.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("volunteer_id", sa.UUID(), sa.ForeignKey("volunteers.id", ondelete="SET NULL"),
                  nullable=True),
        sa.Column("assessment_date", sa.String(20), nullable=False),
        sa.Column("assessment_type", sa.String(50), default="routine"),
        sa.Column("height_cm", sa.Float()),
        sa.Column("weight_kg", sa.Float()),
        sa.Column("bmi", sa.Float()),
        sa.Column("waist_cm", sa.Float()),
        sa.Column("bp_systolic", sa.Float()),
        sa.Column("bp_diastolic", sa.Float()),
        sa.Column("pulse_rate", sa.Float()),
        sa.Column("temperature_c", sa.Float()),
        sa.Column("blood_sugar", sa.Float()),
        sa.Column("notes", sa.Text()),
        sa.Column("is_deleted", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
    )
    op.create_index("ix_health_assessments_citizen_id", "health_assessments", ["citizen_id"])
    op.create_index("ix_health_assessments_date", "health_assessments", ["assessment_date"])

    # early_warnings
    op.create_table(
        "early_warnings",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("citizen_id", sa.UUID(), sa.ForeignKey("citizens.id", ondelete="CASCADE"),
                  nullable=True),
        sa.Column("alert_type", sa.String(100), nullable=False),
        sa.Column("severity", sa.String(20), default="low"),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("detail", sa.Text()),
        sa.Column("status", sa.String(20), default="open"),
        sa.Column("resolved_by", sa.String(200)),
        sa.Column("is_deleted", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
    )
    op.create_index("ix_early_warnings_citizen_id", "early_warnings", ["citizen_id"])
    op.create_index("ix_early_warnings_severity", "early_warnings", ["severity"])

    # cvi_scores
    op.create_table(
        "cvi_scores",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("citizen_id", sa.UUID(), sa.ForeignKey("citizens.id", ondelete="CASCADE"),
                  unique=True, nullable=False),
        sa.Column("score", sa.Float(), default=0.0),
        sa.Column("category", sa.String(20), default="low"),
        sa.Column("age_score", sa.Float(), default=0.0),
        sa.Column("social_score", sa.Float(), default=0.0),
        sa.Column("health_score", sa.Float(), default=0.0),
        sa.Column("environment_score", sa.Float(), default=0.0),
        sa.Column("last_calculated", sa.String(20)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
    )
    op.create_index("ix_cvi_scores_citizen_id", "cvi_scores", ["citizen_id"])
    op.create_index("ix_cvi_scores_category", "cvi_scores", ["category"])


def downgrade() -> None:
    for tbl in ["cvi_scores", "early_warnings", "health_assessments", "health_profiles"]:
        op.drop_table(tbl)
