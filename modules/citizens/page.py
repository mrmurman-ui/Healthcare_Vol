import pandas as pd
import streamlit as st
from sqlalchemy import select

from app.core.db_sync import get_sync_db
from app.modules.auth.session import get_current_user
from app.modules.citizens.model import Citizen
from app.modules.localization.service import t
from app.shared.date_utils import fmt_date, be_date_input
from app.shared.enum_labels import (
    income_labels, housing_labels, gender_labels,
    volunteer_status_labels, referral_status_labels,
    referral_target_labels, visit_type_labels,
    task_status_labels, task_priority_labels,
    assessment_type_labels,
)
from app.shared.enums import Gender


def _t(th: str, en: str) -> str:
    import streamlit as _st
    return th if _st.session_state.get("lang", "TH") == "TH" else en


def render_citizens() -> None:
    st.header(t("nav_citizens"))
    query = st.text_input(t("search"), key="cit_search")

    with get_sync_db() as db:
        stmt = select(Citizen)
        if query:
            stmt = stmt.where(Citizen.full_name.ilike(f"%{query}%"))
        citizens = db.execute(stmt).scalars().all()

    if citizens:
        df = pd.DataFrame([{
            t("name"): c.full_name,
            t("cit_gender"): c.gender or "",
            t("cit_dob"): fmt_date(c.date_of_birth),
            t("phone"): c.phone or "",
            t("cit_elderly"): "✓" if c.is_elderly else "",
            t("cit_disabled"): "✓" if c.is_disabled else "",
            t("cit_bedridden"): "✓" if c.is_bedridden else "",
        } for c in citizens])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info(_t("ไม่พบข้อมูลประชาชน", "No citizens found."))

    st.divider()
    with st.expander(f"➕ {t('add')} " + _t("ประชาชน", "Citizen")):
        with st.form("add_citizen"):
            name = st.text_input(t("name"))
            gender = st.selectbox(t("cit_gender"), [e.value for e in Gender],
                                  format_func=lambda x: gender_labels().get(x, x))
            dob = be_date_input(t("cit_dob"))
            phone = st.text_input(t("phone"))
            occupation = st.text_input(t("cit_occupation"))
            col1, col2, col3, col4, col5 = st.columns(5)
            elderly = col1.checkbox(t("cit_elderly"))
            disabled = col2.checkbox(t("cit_disabled"))
            bedridden = col3.checkbox(t("cit_bedridden"))
            pregnant = col4.checkbox(t("cit_pregnant"))
            alone = col5.checkbox(t("cit_alone"))
            submitted = st.form_submit_button(t("save"))

        if submitted and name:
            user = get_current_user()
            actor = user.email if user else "system"
            with get_sync_db() as db:
                db.add(Citizen(
                    full_name=name, gender=gender,
                    date_of_birth=dob, phone=phone,
                    occupation=occupation,
                    is_elderly=elderly, is_disabled=disabled,
                    is_bedridden=bedridden, is_pregnant=pregnant,
                    is_living_alone=alone,
                    created_by=actor, updated_by=actor,
                ))
            st.success(_t("เพิ่มข้อมูลประชาชนสำเร็จ", "Citizen added."))
            st.rerun()
