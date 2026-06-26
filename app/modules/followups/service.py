"""Follow-up engine — generates follow-ups based on rules."""
from __future__ import annotations


def _t(th: str, en: str) -> str:
    import streamlit as _st
    return th if _st.session_state.get("lang","TH") == "TH" else en


from datetime import date, timedelta

import pandas as pd
import streamlit as st
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.db_sync import get_sync_db
from app.modules.followups.model import Followup
from app.modules.localization.service import t

FOLLOWUP_TYPES = [
    "citizen_not_visited",
    "referral_unresolved",
    "volunteer_inactive",
]

FOLLOWUP_TYPE_TH = {
    "citizen_not_visited": "ประชาชนไม่ได้รับการเยี่ยม",
    "referral_unresolved": "การส่งต่อยังไม่เสร็จสิ้น",
    "volunteer_inactive": "อาสาสมัครไม่ได้ปฏิบัติงาน",
}

FOLLOWUP_STATUS_TH = {
    "pending":     "รอดำเนินการ",
    "in_progress": "กำลังดำเนินการ",
    "completed":   "เสร็จสิ้น",
}

RULE_TRIGGERED_TH = {
    "No visit in 90 days":             "ไม่มีการเยี่ยมบ้านเกิน 90 วัน",
    "Referral unresolved for 30+ days": "การส่งต่อค้างนานเกิน 30 วัน",
    "Volunteer inactive":               "อาสาสมัครไม่ได้ปฏิบัติงาน",
}


# ── Engine ────────────────────────────────────────────────────────────────────

def run_followup_engine(db: Session, actor: str = "system") -> int:
    """Run all follow-up rules. Returns number of new follow-ups created."""
    created = 0

    # Rule 1: Citizens not visited in 90 days
    cutoff = str(date.today() - timedelta(days=90))
    rows = db.execute(text("""
        SELECT c.id FROM citizens c
        WHERE c.is_deleted IS NOT TRUE
        AND NOT EXISTS (
            SELECT 1 FROM home_visits hv
            WHERE hv.citizen_id = c.id
            AND hv.visit_date >= :cutoff
        )
        LIMIT 100
    """), {"cutoff": cutoff}).fetchall()

    for row in rows:
        existing = db.execute(
            select(Followup).where(
                Followup.citizen_id == row[0],
                Followup.followup_type == "citizen_not_visited",
                Followup.status == "pending",
            )
        ).scalar_one_or_none()
        if not existing:
            db.add(Followup(
                citizen_id=row[0],
                followup_type="citizen_not_visited",
                followup_date=str(date.today()),
                status="pending",
                rule_triggered="No visit in 90 days",
                created_by=actor, updated_by=actor,
            ))
            created += 1

    # Rule 2: Referrals unresolved in 30 days
    ref_cutoff = str(date.today() - timedelta(days=30))
    ref_rows = db.execute(text("""
        SELECT id FROM referrals
        WHERE status NOT IN ('completed', 'cancelled')
        AND referral_date::date <= :cutoff
        LIMIT 50
    """), {"cutoff": ref_cutoff}).fetchall()

    for row in ref_rows:
        existing = db.execute(
            select(Followup).where(
                Followup.referral_id == row[0],
                Followup.followup_type == "referral_unresolved",
                Followup.status == "pending",
            )
        ).scalar_one_or_none()
        if not existing:
            db.add(Followup(
                referral_id=row[0],
                followup_type="referral_unresolved",
                followup_date=str(date.today()),
                status="pending",
                rule_triggered="Referral unresolved for 30+ days",
                created_by=actor, updated_by=actor,
            ))
            created += 1

    db.commit()
    return created


# ── Page ─────────────────────────────────────────────────────────────────────

def render_followups() -> None:
    st.header("🔁 " + t("nav_followups"))

    col1, col2 = st.columns([3, 1])
    col1.write(_t("ติดตามอัตโนมัติตามกฎการเยี่ยมบ้านและการส่งต่อ","Automated follow-ups based on visit and referral rules."))

    if col2.button("▶ " + _t("รันเครื่องยนต์","Run Engine")):
        from app.modules.auth.session import get_current_user
        user = get_current_user()
        with get_sync_db() as db:
            count = run_followup_engine(db, actor=user.email if user else "system")
        st.success(_t(f"รันเครื่องยนต์สำเร็จ — สร้างการติดตามใหม่ {count} รายการ", f"Engine ran — {count} new follow-ups created."))
        st.rerun()

    st.divider()

    _is_th = st.session_state.get("lang", "TH") == "TH"
    _status_en = ["", "pending", "in_progress", "completed"]
    _status_display = ["", "รอดำเนินการ", "กำลังดำเนินการ", "เสร็จสิ้น"] if _is_th else _status_en
    _status_idx = st.selectbox(
        _t("กรองตามสถานะ", "Filter by Status"),
        range(len(_status_display)),
        format_func=lambda i: _status_display[i],
    )
    status_filter = _status_en[_status_idx]

    # Profile navigation
    if st.session_state.get("cit_profile_id"):
        from app.modules.citizens.profile import render_citizen_profile
        render_citizen_profile(st.session_state["cit_profile_id"])
        return

    with get_sync_db() as db:
        stmt = select(Followup)
        if status_filter:
            stmt = stmt.where(Followup.status == status_filter)
        stmt = stmt.order_by(Followup.created_at.desc()).limit(200)
        followups = db.execute(stmt).scalars().all()

        # Batch-load citizen names and volunteer names
        cit_ids  = [str(f.citizen_id)   for f in followups if f.citizen_id]
        vol_ids  = [str(f.assigned_to)  for f in followups if f.assigned_to]
        cit_names = {}
        vol_names = {}
        if cit_ids:
            try:
                rows = db.execute(text(
                    "SELECT id::text, full_name FROM citizens WHERE id::text = ANY(:ids)"
                ), {"ids": cit_ids}).fetchall()
                cit_names = {r[0]: r[1] for r in rows}
            except Exception: pass
        if vol_ids:
            try:
                rows = db.execute(text(
                    "SELECT id::text, full_name FROM volunteers WHERE id::text = ANY(:ids)"
                ), {"ids": vol_ids}).fetchall()
                vol_names = {r[0]: r[1] for r in rows}
            except Exception: pass

    if followups:
        _is_th2 = st.session_state.get("lang", "TH") == "TH"
        from app.shared.date_utils import fmt_date

        # Summary metrics
        mc1,mc2,mc3 = st.columns(3)
        mc1.metric("⏳ "+_t("รอดำเนินการ","Pending"),
                   sum(1 for f in followups if f.status=="pending"))
        mc2.metric("🔄 "+_t("กำลังดำเนินการ","In Progress"),
                   sum(1 for f in followups if f.status=="in_progress"))
        mc3.metric("✅ "+_t("เสร็จสิ้น","Completed"),
                   sum(1 for f in followups if f.status=="completed"))
        st.divider()

        # Table header
        h1,h2,h3,h4,h5,h6,h7 = st.columns([2,2,2,2,1,1,1])
        for col,lbl in zip([h1,h2,h3,h4,h5,h6,h7],[
            _t("ประชาชน","Citizen"),
            _t("ประเภท","Type"),
            _t("กฎที่กระตุ้น","Rule"),
            _t("อสม.ผู้ติดตาม","Volunteer"),
            _t("วันที่","Date"),
            _t("สถานะ","Status"),
            "👤",
        ]):
            col.markdown(f"**{lbl}**")
        st.divider()

        for f in followups:
            cid      = str(f.citizen_id) if f.citizen_id else None
            vid      = str(f.assigned_to) if f.assigned_to else None
            cit_name = cit_names.get(cid, "—") if cid else "—"
            vol_name = vol_names.get(vid, vid or "—") if vid else "—"
            ftype    = FOLLOWUP_TYPE_TH.get(f.followup_type, f.followup_type) if _is_th2 else f.followup_type
            rule     = RULE_TRIGGERED_TH.get(f.rule_triggered or "", f.rule_triggered or "") if _is_th2 else (f.rule_triggered or "")
            stat     = FOLLOWUP_STATUS_TH.get(f.status, f.status) if _is_th2 else f.status
            stat_icon= {"pending":"⏳","in_progress":"🔄","completed":"✅"}.get(f.status,"")

            c1,c2,c3,c4,c5,c6,c7 = st.columns([2,2,2,2,1,1,1])
            c1.markdown(f"**{cit_name}**")
            c2.markdown(ftype)
            c3.markdown(rule[:30])
            c4.markdown(f"🙋 {vol_name}" if vol_name != "—" else "—")
            c5.markdown(fmt_date(f.followup_date))
            c6.markdown(f"{stat_icon} {stat}")
            if cid and c7.button("👤", key=f"fu_prof_{f.id}",
                                  help=_t("ดูโปรไฟล์","View Profile")):
                st.session_state["cit_profile_id"] = cid
                st.rerun()

        st.divider()
        st.caption(_t(f"ทั้งหมด: {len(followups)} รายการ",
                      f"Total: {len(followups)} follow-ups"))
    else:
        st.info(_t(
            "ยังไม่มีการติดตาม กดปุ่ม 'รันเครื่องยนต์' เพื่อสร้างรายการติดตามอัตโนมัติ",
            "No follow-ups yet. Click 'Run Engine' to generate them."
        ))
