# -*- coding: utf-8 -*-
"""Early Warning System + CVI — full Thai/EN bilingual."""
from __future__ import annotations
import streamlit as st
from sqlalchemy import func, select, text
from app.core.db_sync import get_sync_db
from app.modules.auth.session import get_current_user


def _t(th: str, en: str) -> str:
    return th if st.session_state.get("lang","TH") == "TH" else en


SEV_LABELS = {
    "critical": ("🚨 วิกฤต",   "🚨 Critical"),
    "high":     ("🔴 สูง",     "🔴 High"),
    "medium":   ("🟠 ปานกลาง", "🟠 Medium"),
    "low":      ("🟡 ต่ำ",     "🟡 Low"),
}
STATUS_LABELS = {
    "open":         ("เปิด",        "Open"),
    "acknowledged": ("รับทราบแล้ว", "Acknowledged"),
    "resolved":     ("แก้ไขแล้ว",  "Resolved"),
}
TYPE_LABELS = {
    "no_visit":             ("ไม่มีการเยี่ยมบ้าน", "No home visit"),
    "homebound_no_caregiver":("ติดบ้านไม่มีผู้ดูแล","Homebound, no caregiver"),
    "open_referral":        ("การส่งต่อค้างนาน",   "Open referral"),
    "bedridden_alone":      ("ติดเตียงอยู่คนเดียว", "Bedridden, alone"),
    "no_assessment":        ("ไม่มีการประเมิน",     "No assessment"),
    "weight_loss":          ("น้ำหนักลดผิดปกติ",   "Abnormal weight loss"),
    "social_isolation":     ("โดดเดี่ยวทางสังคม",   "Social isolation"),
}


def render_early_warning() -> None:
    from app.modules.early_warning.model import EarlyWarning
    from app.modules.citizens.model import Citizen

    is_thai = st.session_state.get("lang","TH") == "TH"

    # ── KPI cards ─────────────────────────────────────────────────────────────
    with get_sync_db() as db:
        try:
            rows = db.execute(
                select(EarlyWarning.severity, func.count())
                .where(EarlyWarning.is_deleted == False, EarlyWarning.status == "open")
                .group_by(EarlyWarning.severity)
            ).all()
            sev_map = {r[0]: r[1] for r in rows}

            status_rows = db.execute(
                select(EarlyWarning.status, func.count())
                .where(EarlyWarning.is_deleted == False)
                .group_by(EarlyWarning.status)
            ).all()
            st_map = {r[0]: r[1] for r in status_rows}

            # Load alerts for list
            alerts = db.execute(
                select(EarlyWarning)
                .where(EarlyWarning.is_deleted == False)
                .order_by(EarlyWarning.created_at.desc())
                .limit(200)
            ).scalars().all()
        except Exception as e:
            st.error(f"Database error: {e}")
            return

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("🚨 " + _t("วิกฤต","Critical"),   sev_map.get("critical",0))
    c2.metric("🔴 " + _t("สูง","High"),          sev_map.get("high",0))
    c3.metric("🟠 " + _t("ปานกลาง","Medium"),    sev_map.get("medium",0))
    c4.metric("🟡 " + _t("ต่ำ","Low"),           sev_map.get("low",0))

    st.divider()

    col1, col2 = st.columns([2, 1])

    # ── Alert list ────────────────────────────────────────────────────────────
    with col1:
        st.subheader(_t("📋 รายการการแจ้งเตือน","📋 Alert List"))

        # Filters
        fc1, fc2, fc3 = st.columns(3)
        sev_filter = fc1.selectbox(
            _t("ระดับความรุนแรง","Severity"),
            [_t("ทั้งหมด","All"), _t("วิกฤต","Critical"),
             _t("สูง","High"), _t("ปานกลาง","Medium"), _t("ต่ำ","Low")],
            key="ew_sev"
        )
        st_filter = fc2.selectbox(
            _t("สถานะ","Status"),
            [_t("ทั้งหมด","All"), _t("เปิด","Open"),
             _t("รับทราบแล้ว","Acknowledged"), _t("แก้ไขแล้ว","Resolved")],
            key="ew_st"
        )

        if alerts:
            import pandas as pd
            sev_map2 = {"วิกฤต":"critical","Critical":"critical",
                        "สูง":"high","High":"high",
                        "ปานกลาง":"medium","Medium":"medium",
                        "ต่ำ":"low","Low":"low"}
            st_map2 = {"เปิด":"open","Open":"open",
                       "รับทราบแล้ว":"acknowledged","Acknowledged":"acknowledged",
                       "แก้ไขแล้ว":"resolved","Resolved":"resolved"}

            filtered = alerts
            if sev_filter not in (_t("ทั้งหมด","All"),):
                fk = sev_map2.get(sev_filter, sev_filter)
                filtered = [a for a in filtered if a.severity == fk]
            if st_filter not in (_t("ทั้งหมด","All"),):
                sk = st_map2.get(st_filter, st_filter)
                filtered = [a for a in filtered if a.status == sk]

            # Load citizen names for all alerts
            from sqlalchemy import text as _text_ew
            ew_cit_ids = [str(a.citizen_id) for a in filtered if a.citizen_id]
            ew_cit_names = {}
            if ew_cit_ids:
                with get_sync_db() as _ewdb:
                    _crows = _ewdb.execute(_text_ew(
                        "SELECT id::text, full_name FROM citizens WHERE id::text = ANY(:ids)"
                    ), {"ids": ew_cit_ids}).fetchall()
                    ew_cit_names = {str(r[0]): r[1] for r in _crows}

            # Render alert rows with citizen name + profile button
            # Table header
            _h1,_h2,_h3,_h4,_h5,_h6,_h7 = st.columns([1,2,3,2,1,1,1])
            for _hcol, _hlbl in zip([_h1,_h2,_h3,_h4,_h5,_h6,_h7],[
                _t("ระดับ","Sev."),
                _t("ประชาชน","Citizen"),
                _t("หัวข้อ","Title"),
                _t("ประเภท","Type"),
                _t("สถานะ","Status"),
                _t("วันที่","Date"),
                "👤",
            ]):
                _hcol.markdown(f"**{_hlbl}**")
            st.divider()

            for a in filtered:
                _sev_lbl = SEV_LABELS.get(a.severity,("",""))[0 if is_thai else 1]
                _type_lbl = TYPE_LABELS.get(a.alert_type,(a.alert_type,a.alert_type))[0 if is_thai else 1]
                _stat_lbl = STATUS_LABELS.get(a.status,(a.status,a.status))[0 if is_thai else 1]
                _cit_name = ew_cit_names.get(str(a.citizen_id),"—") if a.citizen_id else "—"
                _date_str = str(a.created_at or "")[:10]

                _r1,_r2,_r3,_r4,_r5,_r6,_r7 = st.columns([1,2,3,2,1,1,1])
                _r1.markdown(_sev_lbl)
                _r2.markdown(f"**{_cit_name}**")
                _r3.markdown((a.title or a.alert_type)[:60])
                _r4.markdown(_type_lbl[:25])
                _r5.markdown(_stat_lbl)
                _r6.markdown(_date_str)
                if a.citizen_id and _r7.button("👤", key=f"ew_prof_{a.id}",
                                               help=_t("ดูโปรไฟล์","View Profile")):
                    st.session_state["cit_profile_id"] = str(a.citizen_id)
                    st.rerun()
                st.divider()
        else:
            st.info(_t("ยังไม่มีการแจ้งเตือน","No alerts yet."))

    # ── Update status panel ───────────────────────────────────────────────────
    with col2:
        st.subheader(_t("✏️ อัพเดทสถานะ","✏️ Update Alert Status"))
        if alerts:
            open_alerts = [a for a in alerts if a.status != "resolved"]
            if open_alerts:
                alert_opts = {
                    f"{SEV_LABELS.get(a.severity,('',''))[0 if is_thai else 1]} — {a.title or a.alert_type}": a.id
                    for a in open_alerts[:50]
                }
                sel_alert_label = st.selectbox(
                    _t("เลือกการแจ้งเตือน","Select Alert"), list(alert_opts.keys())
                )
                sel_alert_id = alert_opts[sel_alert_label]
                new_status = st.selectbox(
                    _t("สถานะใหม่","New Status"),
                    options=["open","acknowledged","resolved"],
                    format_func=lambda x: STATUS_LABELS.get(x,("",""))[0 if is_thai else 1]
                )
                if st.button(_t("✔ บันทึกสถานะ","✔ Update Status"),
                             type="primary", use_container_width=True):
                    try:
                        actor = get_current_user().email if get_current_user() else "system"
                        with get_sync_db() as db:
                            a = db.get(EarlyWarning, sel_alert_id)
                            if a:
                                a.status = new_status
                                a.updated_by = actor
                        st.success("✅ " + _t("อัพเดทแล้ว","Updated."))
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.info(_t("ไม่มีการแจ้งเตือนที่เปิดอยู่","No open alerts."))

        st.divider()
        st.subheader(_t("📊 สรุปสถานะ","📊 Status Summary"))
        for s_key, s_pair in STATUS_LABELS.items():
            s_label = s_pair[0] if is_thai else s_pair[1]
            st.metric(s_label, st_map.get(s_key, 0))

        if st.button(_t("⚙️ รัน Warning Engine","⚙️ Run Warning Engine"),
                     use_container_width=True):
            with st.spinner(_t("กำลังวิเคราะห์...","Analyzing...")):
                try:
                    from app.modules.early_warning.engine import run_warning_engine
                    with get_sync_db() as db:
                        new_alerts = run_warning_engine(db)
                    st.success(f"✅ " + _t(f"พบ {new_alerts} การแจ้งเตือนใหม่",
                                           f"Found {new_alerts} new alerts."))
                    st.rerun()
                except Exception as e:
                    st.error(f"Engine error: {e}")


def render_cvi() -> None:
    """CVI Scores page — full Thai/EN."""
    from app.modules.early_warning.model import CVIScore
    from app.modules.citizens.model import Citizen

    is_thai = st.session_state.get("lang","TH") == "TH"

    st.info(_t(
        "CVI คือคะแนนลำดับความสำคัญในการสนับสนุนชุมชน (0-100) ไม่ใช่การประเมินความเสี่ยงทางการแพทย์",
        "CVI is a community support priority score (0-100). Not a medical risk assessment."
    ))

    with get_sync_db() as db:
        try:
            rows = db.execute(
                select(CVIScore.category, func.count())
                .group_by(CVIScore.category)
            ).all()
            cat_map = {r[0]: r[1] for r in rows}
            scores = db.execute(
                select(CVIScore)
                .order_by(CVIScore.score.desc()).limit(200)
            ).scalars().all()
        except Exception as e:
            st.error(f"Database error: {e}")
            return

    # KPIs
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("🚨 " + _t("ลำดับวิกฤต","Critical Priority"),  cat_map.get("critical",0))
    c2.metric("🔴 " + _t("ลำดับสูง","High Priority"),         cat_map.get("high",0))
    c3.metric("🟠 " + _t("ลำดับปานกลาง","Moderate Priority"), cat_map.get("moderate",0))
    c4.metric("🟢 " + _t("ลำดับต่ำ","Low Priority"),          cat_map.get("low",0))

    st.divider()

    cat_filter = st.selectbox(
        _t("กรองหมวดหมู่","Filter Category"),
        [_t("ทั้งหมด","All"), _t("วิกฤต","critical"),
         _t("สูง","high"), _t("ปานกลาง","moderate"), _t("ต่ำ","low")]
    )

    if not scores:
        st.info(_t(
            "ยังไม่มีคะแนน CVI กรุณากด 'คำนวณ CVI ใหม่' จากหน้าระบบเตือนภัย",
            "No CVI scores yet. Run 'Recalculate CVI' from the Early Warning page."
        ))
        return

    import pandas as pd
    cat_map_th = {"critical":"วิกฤต","high":"สูง","moderate":"ปานกลาง","low":"ต่ำ"}

    filtered = scores
    filter_map = {_t("วิกฤต","critical"):"critical", _t("สูง","high"):"high",
                  _t("ปานกลาง","moderate"):"moderate", _t("ต่ำ","low"):"low"}
    if cat_filter not in (_t("ทั้งหมด","All"),) and cat_filter in filter_map:
        filtered = [s for s in scores if s.category == filter_map[cat_filter]]

    with get_sync_db() as db:
        cit_ids = [str(s.citizen_id) for s in filtered[:100]]
        citizens_map = {}
        if cit_ids:
            try:
                rows2 = db.execute(
                    select(Citizen.id, Citizen.full_name)
                    .where(Citizen.id.cast(str).in_(cit_ids) if False
                           else Citizen.id.in_([s.citizen_id for s in filtered[:100]]))
                ).all()
                citizens_map = {str(r[0]): r[1] for r in rows2}
            except Exception:
                pass

    df = pd.DataFrame([{
        _t("ประชาชน","Citizen"): citizens_map.get(str(s.citizen_id), str(s.citizen_id)[:8]),
        _t("คะแนน","Score"):    round(s.score or 0, 1),
        _t("หมวดหมู่","Category"): (cat_map_th.get(s.category, s.category)
                                     if is_thai else s.category),
        _t("อายุ","Age Score"): s.age_score,
        _t("สังคม","Social"):   s.social_score,
        _t("สุขภาพ","Health"):  s.health_score,
        _t("สิ่งแวดล้อม","Env"):s.environment_score,
    } for s in filtered[:100]])
    st.dataframe(df, use_container_width=True, hide_index=True)
