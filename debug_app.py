"""Minimal diagnostic app - run this to find the exact error."""
import streamlit as st

st.set_page_config(page_title="Debug", layout="wide")
st.title("Debug - Step by Step")

# Step 1
try:
    from app.core.config import settings
    st.success(f"Step 1 OK: config loaded, APP_ENV={settings.APP_ENV}")
except Exception as e:
    st.error(f"Step 1 FAILED: config - {e}")
    st.stop()

# Step 2
try:
    from app.core.db_sync import get_sync_db
    st.success("Step 2 OK: db_sync imported")
except Exception as e:
    st.error(f"Step 2 FAILED: db_sync - {e}")
    st.stop()

# Step 3
try:
    from sqlalchemy import text
    with get_sync_db() as db:
        result = db.execute(text("SELECT 1")).scalar()
    st.success(f"Step 3 OK: DB connected, result={result}")
except Exception as e:
    st.error(f"Step 3 FAILED: DB connection - {e}")
    st.stop()

# Step 4
try:
    from app.modules.auth.session import is_authenticated, get_current_user
    st.success("Step 4 OK: auth imported")
except Exception as e:
    st.error(f"Step 4 FAILED: auth - {e}")
    st.stop()

# Step 5
try:
    from app.modules.localization.service import t, set_locale
    st.success(f"Step 5 OK: localization loaded, t('save')={t('save')}")
except Exception as e:
    st.error(f"Step 5 FAILED: localization - {e}")
    st.stop()

# Step 6
try:
    from app.modules.dashboard.page import render_dashboard
    st.success("Step 6 OK: dashboard imported")
except Exception as e:
    st.error(f"Step 6 FAILED: dashboard import - {e}")
    st.stop()

st.divider()
st.success("ALL STEPS PASSED - App should work!")
st.info("Now testing dashboard render...")

try:
    render_dashboard()
except Exception as e:
    import traceback
    st.error(f"Dashboard render FAILED: {e}")
    st.code(traceback.format_exc())
