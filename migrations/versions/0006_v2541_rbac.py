"""V2.54.1 — RBAC: roles, permissions, role_permissions, user_roles,
user_scopes, user_profiles, login_history

Revision ID: 0006
Revises: 0005
Create Date: 2025-01-06 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # roles
    op.create_table(
        "roles",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("role_code", sa.String(50), unique=True, nullable=False),
        sa.Column("role_name_th", sa.String(200), nullable=False),
        sa.Column("role_name_en", sa.String(200), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("is_deleted", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
    )
    op.create_index("ix_roles_code", "roles", ["role_code"])

    # permissions
    op.create_table(
        "permissions",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("permission_code", sa.String(100), unique=True, nullable=False),
        sa.Column("module_name", sa.String(100), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
    )
    op.create_index("ix_permissions_code", "permissions", ["permission_code"])

    # role_permissions
    op.create_table(
        "role_permissions",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("role_id", sa.UUID(), sa.ForeignKey("roles.id", ondelete="CASCADE")),
        sa.Column("permission_id", sa.UUID(), sa.ForeignKey("permissions.id", ondelete="CASCADE")),
        sa.Column("is_deleted", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
    )
    op.create_index("ix_role_permissions_role", "role_permissions", ["role_id"])

    # user_roles
    op.create_table(
        "user_roles",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("role_id", sa.UUID(), sa.ForeignKey("roles.id", ondelete="CASCADE")),
        sa.Column("is_primary", sa.Boolean(), default=True),
        sa.Column("is_deleted", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
    )
    op.create_index("ix_user_roles_user", "user_roles", ["user_id"])

    # user_scopes
    op.create_table(
        "user_scopes",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("province_code", sa.String(100)),
        sa.Column("district_code", sa.String(100)),
        sa.Column("subdistrict_code", sa.String(100)),
        sa.Column("village_code", sa.String(100)),
        sa.Column("assigned_by", sa.String(200)),
        sa.Column("assigned_at", sa.DateTime(timezone=True)),
        sa.Column("is_deleted", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
    )
    op.create_index("ix_user_scopes_user", "user_scopes", ["user_id"])

    # user_profiles
    op.create_table(
        "user_profiles",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.String(50), unique=True, nullable=False),
        sa.Column("user_code", sa.String(50), unique=True, nullable=True),
        sa.Column("first_name_th", sa.String(100)),
        sa.Column("last_name_th", sa.String(100)),
        sa.Column("first_name_en", sa.String(100)),
        sa.Column("last_name_en", sa.String(100)),
        sa.Column("phone", sa.String(20)),
        sa.Column("profile_photo", sa.String(500)),
        sa.Column("organization", sa.String(200)),
        sa.Column("position", sa.String(200)),
        sa.Column("license_number", sa.String(100)),
        sa.Column("volunteer_code", sa.String(50)),
        sa.Column("advisor_flag", sa.Boolean(), default=False),
        sa.Column("community_leader_flag", sa.Boolean(), default=False),
        sa.Column("status", sa.String(20), default="active"),
        sa.Column("last_login", sa.DateTime(timezone=True)),
        sa.Column("failed_login_count", sa.Integer(), default=0),
        sa.Column("locked_at", sa.DateTime(timezone=True)),
        sa.Column("password_changed_at", sa.DateTime(timezone=True)),
        sa.Column("force_password_change", sa.Boolean(), default=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", sa.String(200)),
        sa.Column("is_deleted", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
    )
    op.create_index("ix_user_profiles_user_id", "user_profiles", ["user_id"])

    # login_history
    op.create_table(
        "login_history",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="SET NULL"),
                  nullable=True),
        sa.Column("username", sa.String(255), nullable=False),
        sa.Column("login_time", sa.DateTime(timezone=True)),
        sa.Column("logout_time", sa.DateTime(timezone=True)),
        sa.Column("session_duration_minutes", sa.Integer()),
        sa.Column("browser", sa.String(200)),
        sa.Column("operating_system", sa.String(200)),
        sa.Column("ip_address", sa.String(50)),
        sa.Column("login_result", sa.String(20), default="success"),
        sa.Column("failed_attempts", sa.Integer(), default=0),
        sa.Column("is_deleted", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
    )
    op.create_index("ix_login_history_user", "login_history", ["user_id"])
    op.create_index("ix_login_history_username", "login_history", ["username"])


def downgrade() -> None:
    for tbl in ["login_history", "user_profiles", "user_scopes",
                "user_roles", "role_permissions", "permissions", "roles"]:
        op.drop_table(tbl)
