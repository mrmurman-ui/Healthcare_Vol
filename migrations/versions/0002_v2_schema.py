"""V2 schema — tasks, followups, notifications, announcements, community_projects

Revision ID: 0002
Revises: 0001
Create Date: 2025-01-02 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # tasks
    op.create_table(
        "tasks",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("task_code", sa.String(50), nullable=False, unique=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("task_type", sa.String(50), default="home_visit"),
        sa.Column("priority", sa.String(20), default="medium"),
        sa.Column("status", sa.String(20), default="new"),
        sa.Column("due_date", sa.String(20)),
        sa.Column("assigned_to", sa.String(200)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("citizen_id", sa.UUID(), sa.ForeignKey("citizens.id", ondelete="SET NULL"), nullable=True),
        sa.Column("referral_id", sa.UUID(), sa.ForeignKey("referrals.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
    )
    op.create_index("ix_tasks_status", "tasks", ["status"])
    op.create_index("ix_tasks_task_code", "tasks", ["task_code"])

    # followups
    op.create_table(
        "followups",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("citizen_id", sa.UUID(), sa.ForeignKey("citizens.id", ondelete="SET NULL"), nullable=True),
        sa.Column("referral_id", sa.UUID(), sa.ForeignKey("referrals.id", ondelete="SET NULL"), nullable=True),
        sa.Column("followup_type", sa.String(50), nullable=False),
        sa.Column("followup_date", sa.String(20)),
        sa.Column("status", sa.String(20), default="pending"),
        sa.Column("assigned_to", sa.String(200)),
        sa.Column("notes", sa.Text()),
        sa.Column("rule_triggered", sa.String(200)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
    )
    op.create_index("ix_followups_status", "followups", ["status"])
    op.create_index("ix_followups_citizen_id", "followups", ["citizen_id"])

    # notifications
    op.create_table(
        "notifications",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("message", sa.Text()),
        sa.Column("is_read", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])

    # announcements
    op.create_table(
        "announcements",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("content", sa.Text()),
        sa.Column("announcement_type", sa.String(50), default="community_news"),
        sa.Column("target_province", sa.String(100)),
        sa.Column("target_district", sa.String(100)),
        sa.Column("target_subdistrict", sa.String(100)),
        sa.Column("target_village", sa.String(100)),
        sa.Column("start_date", sa.String(20)),
        sa.Column("end_date", sa.String(20)),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
    )

    # community_projects
    op.create_table(
        "community_projects",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("project_code", sa.String(50), nullable=False, unique=True),
        sa.Column("project_name", sa.String(300), nullable=False),
        sa.Column("project_type", sa.String(50), default="other"),
        sa.Column("description", sa.Text()),
        sa.Column("start_date", sa.String(20)),
        sa.Column("end_date", sa.String(20)),
        sa.Column("budget", sa.Float()),
        sa.Column("status", sa.String(20), default="planning"),
        sa.Column("owner", sa.String(200)),
        sa.Column("province", sa.String(100)),
        sa.Column("district", sa.String(100)),
        sa.Column("latitude", sa.Float()),
        sa.Column("longitude", sa.Float()),
        sa.Column("is_deleted", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
    )
    op.create_index("ix_community_projects_status", "community_projects", ["status"])
    op.create_index("ix_community_projects_code", "community_projects", ["project_code"])


def downgrade() -> None:
    for tbl in ["community_projects", "announcements", "notifications", "followups", "tasks"]:
        op.drop_table(tbl)
