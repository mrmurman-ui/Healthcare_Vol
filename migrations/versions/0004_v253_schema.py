"""V2.53 — quality_indicators, quality_records, case_outcomes, risk_scores,
community_scorecards, performance_metrics, capacity_planning

Revision ID: 0004
Revises: 0003
Create Date: 2025-01-04 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # quality_indicators
    op.create_table(
        "quality_indicators",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("indicator_code", sa.String(50), unique=True, nullable=False),
        sa.Column("indicator_name", sa.String(300), nullable=False),
        sa.Column("category", sa.String(50), default="coverage"),
        sa.Column("description", sa.Text()),
        sa.Column("target_value", sa.Float()),
        sa.Column("unit", sa.String(50)),
        sa.Column("period", sa.String(20), default="monthly"),
        sa.Column("active", sa.Boolean(), default=True),
        sa.Column("is_deleted", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
    )
    op.create_index("ix_quality_indicators_code", "quality_indicators", ["indicator_code"])

    # quality_records
    op.create_table(
        "quality_records",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("indicator_id", sa.String(50), nullable=False),
        sa.Column("period_year", sa.Integer(), nullable=False),
        sa.Column("period_month", sa.Integer()),
        sa.Column("period_quarter", sa.Integer()),
        sa.Column("actual_value", sa.Float()),
        sa.Column("notes", sa.Text()),
        sa.Column("is_deleted", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
    )
    op.create_index("ix_quality_records_indicator", "quality_records", ["indicator_id"])

    # case_outcomes
    op.create_table(
        "case_outcomes",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("citizen_id", sa.String(50)),
        sa.Column("case_ref", sa.String(100)),
        sa.Column("outcome_type", sa.String(50), default="ongoing"),
        sa.Column("baseline_value", sa.String(200)),
        sa.Column("current_value", sa.String(200)),
        sa.Column("outcome_status", sa.String(30), default="open"),
        sa.Column("evaluation_date", sa.String(20)),
        sa.Column("notes", sa.Text()),
        sa.Column("is_deleted", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
    )
    op.create_index("ix_case_outcomes_citizen_id", "case_outcomes", ["citizen_id"])

    # risk_scores
    op.create_table(
        "risk_scores",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("citizen_id", sa.String(50), unique=True, nullable=False),
        sa.Column("score", sa.Float(), default=0.0),
        sa.Column("risk_level", sa.String(20), default="low"),
        sa.Column("calculation_date", sa.String(20)),
        sa.Column("factors", sa.Text()),
        sa.Column("is_deleted", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
    )
    op.create_index("ix_risk_scores_citizen_id", "risk_scores", ["citizen_id"])
    op.create_index("ix_risk_scores_level", "risk_scores", ["risk_level"])

    # community_scorecards
    op.create_table(
        "community_scorecards",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("community_id", sa.String(100), nullable=False),
        sa.Column("community_name", sa.String(200), nullable=False),
        sa.Column("district", sa.String(100)),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("population", sa.Integer()),
        sa.Column("coverage_rate", sa.Float()),
        sa.Column("assessment_rate", sa.Float()),
        sa.Column("home_visit_rate", sa.Float()),
        sa.Column("referral_completion_rate", sa.Float()),
        sa.Column("case_closure_rate", sa.Float()),
        sa.Column("volunteer_activity_rate", sa.Float()),
        sa.Column("overall_score", sa.Float()),
        sa.Column("is_deleted", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
    )
    op.create_index("ix_community_scorecards_community", "community_scorecards", ["community_id"])
    op.create_index("ix_community_scorecards_period", "community_scorecards", ["year", "month"])

    # performance_metrics
    op.create_table(
        "performance_metrics",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("metric_name", sa.String(300), nullable=False),
        sa.Column("metric_category", sa.String(100), default="volunteer_productivity"),
        sa.Column("target", sa.Float()),
        sa.Column("current_value", sa.Float()),
        sa.Column("unit", sa.String(50)),
        sa.Column("status", sa.String(30), default="on_track"),
        sa.Column("period", sa.String(20)),
        sa.Column("notes", sa.Text()),
        sa.Column("is_deleted", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
    )

    # capacity_planning
    op.create_table(
        "capacity_planning",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("district", sa.String(100)),
        sa.Column("community", sa.String(100)),
        sa.Column("population", sa.Integer()),
        sa.Column("elderly_population", sa.Integer()),
        sa.Column("volunteers", sa.Integer()),
        sa.Column("active_cases", sa.Integer()),
        sa.Column("workload_score", sa.Float()),
        sa.Column("snapshot_date", sa.String(20)),
        sa.Column("is_deleted", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
    )
    op.create_index("ix_capacity_planning_district", "capacity_planning", ["district"])


def downgrade() -> None:
    for tbl in ["capacity_planning", "performance_metrics", "community_scorecards",
                "risk_scores", "case_outcomes", "quality_records", "quality_indicators"]:
        op.drop_table(tbl)
