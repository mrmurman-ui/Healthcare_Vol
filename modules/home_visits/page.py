from datetime import date

import pandas as pd
import streamlit as st
from sqlalchemy import select

from app.core.db_sync import get_sync_db
from app.modules.auth.session import get_current_user
from app.modules.home_visits.model import HomeVisit
from app.modules.localization.service import t
from app.shared.date_utils import fmt_date, be_date_input
from app.shared.enum_labels import (
    income_labels, housing_labels, gender_labels,
    volunteer_status_labels, referral_status_labels,
    referral_target_labels, visit_type_labels,
    task_status_labels, task_priority_labels,
    assessment_type_labels,
)
from app.shared.enums import VisitType


def _t(th: str, en: str) -> str:
    import streamlit as _st
    return th if _st.session_state.get("lang", "TH") == "TH" else en


def render_home_visits() -> None:
    st.header(t("nav_home_visits"))

    with get_sync_db() as db:
        visits = db.execute(
            select(HomeVisit).order_by(HomeVisit.visit_date.desc()).limit(50)
        ).scalars().all()

    if visits:
        df = pd.DataFrame([{
            t("date"): fmt_date(v.visit_date),
            t("vis_type"): v.visit_type,
            t("vis_observation"): (v.observation or "")[:80],
            t("vis_recommendation"): (v.recommendation or "")[:80],
        } for v in visits])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info(_t("ยังไม่มีการเยี่ยมบ้านที่บันทึก", "No visits recorded."))

    st.divider()
    with st.expander(f"➕ {t('add')} " + _t("การเยี่ยมบ้าน", "Home Visit")):
        with st.form("add_visit"):
            visit_date = be_date_input(t("date"), value=date.today())
            visit_type = st.selectbox(t("vis_type"), [e.value for e in VisitType],
                                      format_func=lambda x: visit_type_labels().get(x, x))
            observation = st.text_area(t("vis_observation"))
            recommendation = st.text_area(t("vis_recommendation"))
            lat = st.number_input("GPS Latitude", value=0.0, format="%.6f")
            lon = st.number_input("GPS Longitude", value=0.0, format="%.6f")
            submitted = st.form_submit_button(t("save"))

        if submitted:
            user = get_current_user()
            actor = user.email if user else "system"
            with get_sync_db() as db:
                db.add(HomeVisit(
                    visit_date=visit_date, visit_type=visit_type,
                    observation=observation, recommendation=recommendation,
                    latitude=lat or None, longitude=lon or None,
                    created_by=actor, updated_by=actor,
                ))
            st.success(_t("บันทึกการเยี่ยมบ้านสำเร็จ", "Visit recorded."))
            st.rerun()
