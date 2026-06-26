"""Alembic environment — synchronous migrations only."""
import os
import re
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

# V1 models
from app.core.database import Base  # noqa: F401
import app.modules.users.model  # noqa: F401
import app.modules.volunteers.model  # noqa: F401
import app.modules.households.model  # noqa: F401
import app.modules.citizens.model  # noqa: F401
import app.modules.home_visits.model  # noqa: F401
import app.modules.referrals.model  # noqa: F401
import app.modules.audit.service  # noqa: F401
# V2 models
import app.modules.tasks.model  # noqa: F401
import app.modules.followups.model  # noqa: F401
import app.modules.notifications.service  # noqa: F401
import app.modules.announcements.service  # noqa: F401
import app.modules.community_projects.service  # noqa: F401
import app.modules.health_profiles.model  # noqa: F401
import app.modules.health_assessments.model  # noqa: F401
import app.modules.early_warning.model  # noqa: F401

config = context.config

if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _get_url() -> str:
    raw = (
        os.environ.get("DATABASE_URL_SYNC")
        or os.environ.get("DATABASE_URL")
        or config.get_main_option("sqlalchemy.url", "")
    )
    raw = re.sub(r"postgresql\+asyncpg://", "postgresql+psycopg2://", raw)
    raw = re.sub(r"sqlite\+aiosqlite://", "sqlite://", raw)
    raw = re.sub(r"[&?]sslrootcert=[^&]*", "", raw)
    if "sslmode=" not in raw:
        raw += ("&" if "?" in raw else "?") + "sslmode=require"
    return raw


def run_migrations_offline() -> None:
    context.configure(
        url=_get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(_get_url(), poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
# NOTE: V2.51 models imported via service files which define models inline
# V2.54 models
import app.modules.settings.service  # noqa: F401
import app.modules.feature_flags.service  # noqa: F401
import app.modules.application_logs.service  # noqa: F401
import app.modules.error_tracking.service  # noqa: F401
