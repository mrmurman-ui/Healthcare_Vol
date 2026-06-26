"""initial schema

Revision ID: 0001
Revises:
Create Date: 2025-01-01 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("province", sa.String(100)),
        sa.Column("district", sa.String(100)),
        sa.Column("subdistrict", sa.String(100)),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # volunteers
    op.create_table(
        "volunteers",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("volunteer_code", sa.String(50), nullable=False, unique=True),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("phone", sa.String(20)),
        sa.Column("email", sa.String(255)),
        sa.Column("province", sa.String(100)),
        sa.Column("district", sa.String(100)),
        sa.Column("subdistrict", sa.String(100)),
        sa.Column("village", sa.String(100)),
        sa.Column("position", sa.String(100)),
        sa.Column("status", sa.String(20), default="active"),
        sa.Column("photo_url", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
    )

    # households
    op.create_table(
        "households",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("household_code", sa.String(50), nullable=False, unique=True),
        sa.Column("address", sa.String(500)),
        sa.Column("village", sa.String(100)),
        sa.Column("community", sa.String(100)),
        sa.Column("subdistrict", sa.String(100)),
        sa.Column("district", sa.String(100)),
        sa.Column("province", sa.String(100)),
        sa.Column("latitude", sa.Float()),
        sa.Column("longitude", sa.Float()),
        sa.Column("head_of_household", sa.String(200)),
        sa.Column("phone", sa.String(20)),
        sa.Column("income_group", sa.String(20)),
        sa.Column("housing_type", sa.String(20)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
    )

    # citizens
    op.create_table(
        "citizens",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("household_id", sa.UUID(), sa.ForeignKey("households.id", ondelete="SET NULL"), nullable=True),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("gender", sa.String(10)),
        sa.Column("date_of_birth", sa.Date()),
        sa.Column("occupation", sa.String(100)),
        sa.Column("education", sa.String(100)),
        sa.Column("phone", sa.String(20)),
        sa.Column("is_elderly", sa.Boolean(), default=False),
        sa.Column("is_disabled", sa.Boolean(), default=False),
        sa.Column("is_bedridden", sa.Boolean(), default=False),
        sa.Column("is_pregnant", sa.Boolean(), default=False),
        sa.Column("is_living_alone", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
    )

    # home_visits
    op.create_table(
        "home_visits",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("citizen_id", sa.UUID(), sa.ForeignKey("citizens.id", ondelete="SET NULL"), nullable=True),
        sa.Column("volunteer_id", sa.UUID(), sa.ForeignKey("volunteers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("visit_date", sa.Date(), nullable=False),
        sa.Column("visit_type", sa.String(20), default="routine"),
        sa.Column("observation", sa.Text()),
        sa.Column("recommendation", sa.Text()),
        sa.Column("latitude", sa.Float()),
        sa.Column("longitude", sa.Float()),
        sa.Column("photo_urls", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
    )

    # referrals
    op.create_table(
        "referrals",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("citizen_id", sa.UUID(), sa.ForeignKey("citizens.id", ondelete="SET NULL"), nullable=True),
        sa.Column("volunteer_id", sa.UUID(), sa.ForeignKey("volunteers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("referral_date", sa.Date(), nullable=False),
        sa.Column("target", sa.String(30), nullable=False),
        sa.Column("target_name", sa.String(200)),
        sa.Column("reason", sa.Text()),
        sa.Column("status", sa.String(20), default="pending"),
        sa.Column("outcome", sa.Text()),
        sa.Column("followup_date", sa.Date()),
        sa.Column("followup_notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
    )

    # audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("actor", sa.String(200), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", sa.String(100)),
        sa.Column("detail", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    for tbl in ["audit_logs", "referrals", "home_visits", "citizens", "households", "volunteers", "users"]:
        op.drop_table(tbl)
