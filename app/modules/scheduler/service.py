"""Job Scheduler — APScheduler-based background jobs. No Celery, no Redis."""
from __future__ import annotations

import threading
from datetime import datetime, UTC

import pandas as pd
import streamlit as st

from app.modules.localization.service import t
from app.shared.enums import UserRole

_scheduler = None
_jobs_log: list[dict] = []
_lock = threading.Lock()


def _get_scheduler():
    global _scheduler
    if _scheduler is None:
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            _scheduler = BackgroundScheduler(timezone="Asia/Bangkok")
            _scheduler.start()
        except ImportError:
            pass
    return _scheduler


def _log_job(job_name: str, status: str, detail: str = "") -> None:
    with _lock:
        _jobs_log.append({
            "time": str(datetime.now(UTC))[:19],
            "job": job_name,
            "status": status,
            "detail": detail,
        })
        if len(_jobs_log) > 200:
            _jobs_log.pop(0)


# ── Job definitions ───────────────────────────────────────────────────────────

def _job_followup_engine() -> None:
    try:
        from app.core.db_sync import get_sync_db
        from app.modules.followups.service import run_followup_engine
        with get_sync_db() as db:
            count = run_followup_engine(db, actor="scheduler")
        _log_job("follow_up_engine", "success", f"{count} follow-ups created")
    except Exception as e:
        _log_job("follow_up_engine", "error", str(e))


def _job_warning_engine() -> None:
    try:
        from app.core.db_sync import get_sync_db
        from app.modules.early_warning.service import run_warning_engine
        with get_sync_db() as db:
            count = run_warning_engine(db, actor="scheduler")
        _log_job("warning_engine", "success", f"{count} alerts created")
    except Exception as e:
        _log_job("warning_engine", "error", str(e))


def _job_cvi_recalc() -> None:
    try:
        from app.core.db_sync import get_sync_db
        from app.modules.early_warning.service import run_cvi_engine
        with get_sync_db() as db:
            count = run_cvi_engine(db, actor="scheduler")
        _log_job("cvi_recalculate", "success", f"{count} citizens updated")
    except Exception as e:
        _log_job("cvi_recalculate", "error", str(e))


def _job_risk_recalc() -> None:
    try:
        from app.core.db_sync import get_sync_db
        from app.modules.risk_stratification.service import run_risk_engine
        with get_sync_db() as db:
            count = run_risk_engine(db, actor="scheduler")
        _log_job("risk_recalculate", "success", f"{count} scores updated")
    except Exception as e:
        _log_job("risk_recalculate", "error", str(e))


SCHEDULED_JOBS = [
    {
        "id": "followup_engine_daily",
        "name": "Daily Follow-Up Engine",
        "fn": _job_followup_engine,
        "trigger": "cron",
        "hour": 6, "minute": 0,
        "frequency": "Daily 06:00",
    },
    {
        "id": "warning_engine_daily",
        "name": "Daily Warning Engine",
        "fn": _job_warning_engine,
        "trigger": "cron",
        "hour": 6, "minute": 30,
        "frequency": "Daily 06:30",
    },
    {
        "id": "cvi_weekly",
        "name": "Weekly CVI Recalculation",
        "fn": _job_cvi_recalc,
        "trigger": "cron",
        "day_of_week": "mon", "hour": 2, "minute": 0,
        "frequency": "Weekly Monday 02:00",
    },
    {
        "id": "risk_weekly",
        "name": "Weekly Risk Recalculation",
        "fn": _job_risk_recalc,
        "trigger": "cron",
        "day_of_week": "mon", "hour": 3, "minute": 0,
        "frequency": "Weekly Monday 03:00",
    },
]


def start_scheduler() -> bool:
    """Start all scheduled jobs. Call once at app startup."""
    sched = _get_scheduler()
    if sched is None:
        return False
    try:
        for job in SCHEDULED_JOBS:
            if not sched.get_job(job["id"]):
                kwargs = {k: v for k, v in job.items()
                          if k not in ("id", "name", "fn", "frequency")}
                sched.add_job(job["fn"], id=job["id"], **kwargs)
        return True
    except Exception:
        return False


def render_scheduler() -> None:
    from app.modules.auth.session import assert_roles
    assert_roles(UserRole.SUPER_ADMIN, UserRole.PROVINCE_ADMIN)
    st.header("⏰ " + t("nav_scheduler"))

    sched = _get_scheduler()
    status = "✅ Running" if sched and sched.running else "❌ Not Running"
    st.metric("Scheduler Status", status)

    if st.button("▶ Start Scheduler"):
        started = start_scheduler()
        if started:
            st.success("Scheduler started.")
        else:
            st.warning("APScheduler not available. Install: pip install apscheduler")

    st.divider()
    st.subheader("Scheduled Jobs")

    job_rows = []
    for job in SCHEDULED_JOBS:
        next_run = "—"
        if sched:
            j = sched.get_job(job["id"])
            if j and j.next_run_time:
                next_run = str(j.next_run_time)[:19]
        job_rows.append({
            "Job": job["name"],
            "Frequency": job["frequency"],
            "Next Run": next_run,
        })

    st.dataframe(pd.DataFrame(job_rows), use_container_width=True, hide_index=True)

    col1, col2, col3, col4 = st.columns(4)
    if col1.button("▶ Run Follow-Up Now"):
        _job_followup_engine()
        st.success("Follow-up engine ran.")
    if col2.button("▶ Run Warning Engine"):
        _job_warning_engine()
        st.success("Warning engine ran.")
    if col3.button("▶ Recalc CVI"):
        _job_cvi_recalc()
        st.success("CVI recalculated.")
    if col4.button("▶ Recalc Risk"):
        _job_risk_recalc()
        st.success("Risk recalculated.")

    st.divider()
    st.subheader("Job Run History (Session)")
    with _lock:
        log_copy = list(reversed(_jobs_log[-50:]))
    if log_copy:
        df = pd.DataFrame(log_copy)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No jobs run yet in this session.")
