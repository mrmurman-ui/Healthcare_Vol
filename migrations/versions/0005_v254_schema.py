"""V2.54 — system_settings, feature_flags, app_logs, system_errors

Revision ID: 0005
Revises: 0004
Create Date: 2025-01-05 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # system_settings
    op.create_table(
        "system_settings",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("key", sa.String(100), unique=True, nullable=False),
        sa.Column("value", sa.Text()),
        sa.Column("description", sa.String(300)),
        sa.Column("is_secret", sa.Boolean(), default=False),
        sa.Column("is_deleted", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
    )
    op.create_index("ix_system_settings_key", "system_settings", ["key"])

    # feature_flags
    op.create_table(
        "feature_flags",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("key", sa.String(100), unique=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("enabled", sa.Boolean(), default=True),
        sa.Column("description", sa.Text()),
        sa.Column("is_deleted", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
    )
    op.create_index("ix_feature_flags_key", "feature_flags", ["key"])

    # app_logs
    op.create_table(
        "app_logs",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("level", sa.String(20), default="INFO"),
        sa.Column("module", sa.String(100)),
        sa.Column("action", sa.String(200), nullable=False),
        sa.Column("user_email", sa.String(255)),
        sa.Column("log_metadata", sa.Text()),
        sa.Column("is_deleted", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
    )
    op.create_index("ix_app_logs_level", "app_logs", ["level"])
    op.create_index("ix_app_logs_module", "app_logs", ["module"])

    # system_errors
    op.create_table(
        "system_errors",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("level", sa.String(20), default="ERROR"),
        sa.Column("module", sa.String(100)),
        sa.Column("message", sa.String(500), nullable=False),
        sa.Column("traceback_text", sa.Text()),
        sa.Column("user_email", sa.String(255)),
        sa.Column("resolved", sa.Boolean(), default=False),
        sa.Column("resolved_by", sa.String(255)),
        sa.Column("notes", sa.Text()),
        sa.Column("is_deleted", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
    )
    op.create_index("ix_system_errors_level", "system_errors", ["level"])
    op.create_index("ix_system_errors_resolved", "system_errors", ["resolved"])


def downgrade() -> None:
    for tbl in ["system_errors", "app_logs", "feature_flags", "system_settings"]:
        op.drop_table(tbl)
