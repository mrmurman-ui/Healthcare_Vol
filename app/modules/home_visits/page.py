"""Home Visits — with citizen name, household, and profile link."""
from datetime import date

import pandas as pd
import streamlit as st
from sqlalchemy import select, text

from app.core.db_sync import get_sync_db
from app.modules.auth.session import get_current_user
from app.modules.citizens.model import Citizen
from app.modules.home_visits.model import HomeVisit
from app.modules.localization.service import t
from app.shared.date_utils import fmt_date, be_date_input
from app.shared.enum_labels import visit_type_labels
from app.shared.enums import VisitType


def _t(th, en): return th if st.session_state.get("lang","TH")=="TH" else en


def render_home_visits() -> None:
    st.header(t("nav_home_visits"))

    # Profile navigation
    if st.session_state.get("cit_profile_id"):
        from app.modules.citizens.profile import render_citizen_profile
        render_citizen_profile(st.session_state["cit_profile_id"])
        return

    _vtl = visit_type_labels()
    is_th = st.session_state.get("lang","TH")=="TH"

    # ── Filters ───────────────────────────────────────────────────────────────
    fc1, fc2, fc3 = st.columns(3)
    f_name = fc1.text_input("🔍 " + _t("ค้นหาชื่อประชาชน","Search Citizen Name"), key="hv_name")
    vtype_opts = [""]+[e.value for e in VisitType]
    f_type = fc2.selectbox(_t("ประเภทการเยี่ยม","Visit Type"), vtype_opts,
                           format_func=lambda x: _t("ทั้งหมด","All") if not x else _vtl.get(x,x))
    f_limit = fc3.selectbox(_t("แสดง","Show"), [50,100,200,500], index=0)

    # ── Query with JOIN to get citizen name and household ─────────────────────
    with get_sync_db() as db:
        sql = text("""
            SELECT
                hv.id,
                hv.visit_date,
                hv.visit_type,
                hv.observation,
                hv.recommendation,
                c.full_name   AS citizen_name,
                c.id          AS citizen_id,
                h.household_code,
                h.head_of_household,
                v.full_name   AS volunteer_name
            FROM home_visits hv
            LEFT JOIN citizens c ON c.id = hv.citizen_id
            LEFT JOIN households h ON h.id = c.household_id
            LEFT JOIN volunteers v ON v.id = hv.volunteer_id
            WHERE (:name = '' OR c.full_name ILIKE '%' || :name || '%')
              AND (:vtype = '' OR hv.visit_type = :vtype)
            ORDER BY hv.visit_date DESC
            LIMIT :lim
        """)
        rows = db.execute(sql, {
            "name": f_name or "",
            "vtype": f_type or "",
            "lim": f_limit,
        }).fetchall()

    if rows:
        st.caption(_t(f"แสดง {len(rows)} รายการ",f"Showing {len(rows)} records"))

        # ── Table header ──────────────────────────────────────────────────────
        h1,h2,h3,h4,h5,h6,h7 = st.columns([1,2,2,1,3,3,1])
        for col, lbl in zip([h1,h2,h3,h4,h5,h6,h7],[
            _t("วันที่","Date"),
            _t("ประชาชน","Citizen"),
            _t("ครอบครัว","Household"),
            _t("ประเภท","Type"),
            _t("การสังเกต","Observation"),
            _t("คำแนะนำ","Recommendation"),
            "👤",
        ]):
            col.markdown(f"**{lbl}**")
        st.divider()

        # ── Rows ──────────────────────────────────────────────────────────────
        for row in rows:
            (vid, vdate, vtype, obs, rec,
             cit_name, cit_id, hh_code, hh_head, vol_name) = row

            c1,c2,c3,c4,c5,c6,c7 = st.columns([1,2,2,1,3,3,1])
            c1.markdown(fmt_date(vdate))
            c2.markdown(f"**{cit_name or '—'}**")
            c3.markdown(f"{hh_code or '—'}" +
                        (f"  \n{hh_head[:15]}" if hh_head else ""))
            c4.markdown(_vtl.get(vtype or "", vtype or "—"))
            c5.markdown((obs or "—")[:60])
            c6.markdown((rec or "—")[:60])

            if cit_id and c7.button("👤", key=f"hv_prof_{vid}",
                                    help=_t("ดูโปรไฟล์","View Profile")):
                st.session_state["cit_profile_id"] = str(cit_id)
                st.rerun()

            if vol_name:
                st.caption(f"🙋 {_t('อสม.','VHV')}: {vol_name}")
            st.divider()
    else:
        st.info(_t("ยังไม่มีการเยี่ยมบ้านที่บันทึก","No visits recorded."))

    # ── Add visit form ─────────────────────────────────────────────────────────
    st.divider()
    with st.expander(f"➕ {t('add')} " + _t("การเยี่ยมบ้าน","Home Visit")):
        with get_sync_db() as db:
            cits = db.execute(select(Citizen).order_by(Citizen.full_name).limit(500)).scalars().all()
        cit_opts = {_t("— ไม่เชื่อมโยง —","— None —"): None}
        cit_opts.update({f"{c.full_name}": str(c.id) for c in cits})

        with st.form("add_visit"):
            sel_cit = st.selectbox(_t("ประชาชน (ไม่บังคับ)","Citizen (optional)"),
                                   list(cit_opts.keys()))
            visit_date   = be_date_input(t("date"), value=date.today(), key="hv_date")
            visit_type   = st.selectbox(t("vis_type"), [e.value for e in VisitType],
                                        format_func=lambda x: visit_type_labels().get(x,x))
            observation    = st.text_area(t("vis_observation"))
            recommendation = st.text_area(t("vis_recommendation"))
            lat = st.number_input("GPS Latitude",  value=0.0, format="%.6f")
            lon = st.number_input("GPS Longitude", value=0.0, format="%.6f")
            submitted = st.form_submit_button(t("save"))

        if submitted:
            user  = get_current_user()
            actor = user.email if user else "system"
            cit_id = cit_opts.get(sel_cit)
            with get_sync_db() as db:
                db.add(HomeVisit(
                    visit_date=visit_date, visit_type=visit_type,
                    observation=observation, recommendation=recommendation,
                    citizen_id=cit_id,
                    latitude=lat or None, longitude=lon or None,
                    created_by=actor, updated_by=actor,
                ))
            st.success(_t("บันทึกการเยี่ยมบ้านสำเร็จ","Visit recorded."))
            st.rerun()
