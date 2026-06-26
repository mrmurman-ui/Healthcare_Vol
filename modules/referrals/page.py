from datetime import date

import pandas as pd
import streamlit as st
from sqlalchemy import select

from app.core.db_sync import get_sync_db
from app.modules.auth.session import get_current_user
from app.modules.localization.service import t
from app.modules.referrals.model import Referral
from app.shared.date_utils import fmt_date, be_date_input
from app.shared.enum_labels import (
    income_labels, housing_labels, gender_labels,
    volunteer_status_labels, referral_status_labels,
    referral_target_labels, visit_type_labels,
    task_status_labels, task_priority_labels,
    assessment_type_labels,
)
from app.shared.enums import ReferralTarget


def _t(th: str, en: str) -> str:
    import streamlit as _st
    return th if _st.session_state.get("lang", "TH") == "TH" else en


def render_referrals() -> None:
    st.header(t("nav_referrals"))

    with get_sync_db() as db:
        referrals = db.execute(
            select(Referral).order_by(Referral.referral_date.desc()).limit(100)
        ).scalars().all()

    if referrals:
        df = pd.DataFrame([{
            t("date"): fmt_date(r.referral_date),
            t("ref_target"): r.target,
            _t("ชื่อสถานที่", "Target Name"): r.target_name or "",
            t("ref_status"): r.status,
            t("ref_outcome"): (r.outcome or "")[:60],
        } for r in referrals])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info(_t("ไม่พบข้อมูลการส่งต่อ", "No referrals found."))

    st.divider()
    with st.expander(f"➕ {t('add')} " + _t("การส่งต่อ", "Referral")):
        with st.form("add_referral"):
            ref_date = be_date_input(t("date"), value=date.today())
            target = st.selectbox(t("ref_target"), [e.value for e in ReferralTarget],
                                  format_func=lambda x: referral_target_labels().get(x, x))
            target_name = st.text_input(_t("ชื่อสถานที่/หน่วยงาน", "Target Name"))
            reason = st.text_area(_t("เหตุผล", "Reason"))
            submitted = st.form_submit_button(t("save"))

        if submitted:
            user = get_current_user()
            actor = user.email if user else "system"
            with get_sync_db() as db:
                db.add(Referral(
                    referral_date=ref_date, target=target,
                    target_name=target_name, reason=reason,
                    status="pending",
                    created_by=actor, updated_by=actor,
                ))
            st.success(_t("สร้างการส่งต่อสำเร็จ", "Referral created."))
            st.rerun()
