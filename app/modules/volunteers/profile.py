"""Volunteer Profile — full individual view with training history."""
from __future__ import annotations
from datetime import date

import pandas as pd
import streamlit as st
from sqlalchemy import select, text

from app.core.db_sync import get_sync_db
from app.modules.auth.session import get_current_user
from app.modules.volunteers.model import Volunteer
from app.shared.date_utils import fmt_date, be_date_input, ad_to_be_year

def _t(th, en): return th if st.session_state.get("lang","TH")=="TH" else en


def _ensure_tables():
    """Create volunteer_trainings and volunteer_extra tables if not exist."""
    with get_sync_db() as db:
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS volunteer_trainings (
                id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                volunteer_id    UUID NOT NULL REFERENCES volunteers(id) ON DELETE CASCADE,
                training_date   VARCHAR(20),
                topic           VARCHAR(300) NOT NULL,
                organizer       VARCHAR(200),
                duration_hours  FLOAT,
                location        VARCHAR(200),
                certificate_no  VARCHAR(100),
                notes           TEXT,
                is_deleted      BOOLEAN DEFAULT FALSE,
                created_at      TIMESTAMP DEFAULT NOW(),
                updated_at      TIMESTAMP DEFAULT NOW(),
                created_by      VARCHAR(100),
                updated_by      VARCHAR(100)
            )
        """))
        # Extra fields for volunteer profile
        for col, coltype in [
            ("id_card",       "VARCHAR(13)"),
            ("birth_date",    "VARCHAR(20)"),
            ("education",     "VARCHAR(100)"),
            ("occupation",    "VARCHAR(100)"),
            ("start_year",    "INTEGER"),
            ("line_id",       "VARCHAR(100)"),
            ("notes",         "TEXT"),
        ]:
            try:
                db.execute(text(
                    f"ALTER TABLE volunteers ADD COLUMN IF NOT EXISTS {col} {coltype}"
                ))
            except Exception:
                pass


def render_volunteer_profile(volunteer_id: str) -> None:
    _ensure_tables()
    is_th = st.session_state.get("lang","TH")=="TH"

    with get_sync_db() as db:
        vol = db.get(Volunteer, volunteer_id)
        if not vol:
            st.error(_t("ไม่พบข้อมูลอาสาสมัคร","Volunteer not found."))
            return

        trainings = db.execute(text("""
            SELECT id, training_date, topic, organizer,
                   duration_hours, location, certificate_no, notes
            FROM volunteer_trainings
            WHERE volunteer_id=:vid AND (is_deleted IS NULL OR is_deleted=false)
            ORDER BY training_date DESC
        """), {"vid": str(volunteer_id)}).fetchall()

        visit_stats = db.execute(text("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN visit_date >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as last30
            FROM home_visits WHERE volunteer_id=:vid
        """), {"vid": str(volunteer_id)}).fetchone()

        ref_stats = db.execute(text("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN status='completed' THEN 1 END) as done
            FROM referrals WHERE volunteer_id=:vid
        """), {"vid": str(volunteer_id)}).fetchone()

        recent_visits = db.execute(text("""
            SELECT hv.visit_date, hv.visit_type, c.full_name, hv.observation
            FROM home_visits hv
            LEFT JOIN citizens c ON c.id=hv.citizen_id
            WHERE hv.volunteer_id=:vid
            ORDER BY hv.visit_date DESC LIMIT 8
        """), {"vid": str(volunteer_id)}).fetchall()

    # ── Back button ───────────────────────────────────────────────────────────
    if st.button("← " + _t("ย้อนกลับ","Back"), key="vol_prof_back"):
        st.session_state.pop("vol_profile_id", None)
        st.rerun()

    st.divider()

    # ── Hero card ─────────────────────────────────────────────────────────────
    from app.shared.enum_labels import volunteer_status_labels
    vsl = volunteer_status_labels()
    status_color = "#22C55E" if (vol.status or "").lower()=="active" else "#9CA3AF"
    status_lbl   = vsl.get(vol.status or "", vol.status or "")

    st.markdown(f"""
<div style="background:linear-gradient(135deg,#1B3A6B,#0F766E);
  border-radius:16px;padding:28px 32px;color:white;margin-bottom:20px">
  <div style="display:flex;align-items:center;gap:20px">
    <div style="font-size:56px">👤</div>
    <div>
      <div style="font-size:28px;font-weight:800;margin-bottom:4px">{vol.full_name}</div>
      <div style="font-size:16px;opacity:0.9;margin-bottom:6px">
        <code style="background:rgba(255,255,255,0.2);padding:2px 10px;border-radius:10px">
          {vol.volunteer_code}
        </code>
        &nbsp;&nbsp;{vol.position or '—'}
      </div>
      <div style="font-size:14px;opacity:0.8">
        📍 {vol.subdistrict or ''} {vol.district or ''} {vol.province or ''}
        &nbsp;&nbsp;📞 {vol.phone or '—'}
      </div>
    </div>
    <div style="margin-left:auto;text-align:right">
      <span style="background:{status_color};color:white;padding:6px 18px;
        border-radius:20px;font-size:14px;font-weight:600">{status_lbl}</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── KPI row ───────────────────────────────────────────────────────────────
    k1,k2,k3,k4,k5 = st.columns(5)
    k1.metric("🏠 " + _t("เยี่ยมบ้านทั้งหมด","Total Visits"),
              visit_stats[0] if visit_stats else 0)
    k2.metric("📅 " + _t("30 วันล่าสุด","Last 30d"),
              visit_stats[1] if visit_stats else 0)
    k3.metric("📤 " + _t("ส่งต่อทั้งหมด","Referrals"),
              ref_stats[0] if ref_stats else 0)
    k4.metric("✅ " + _t("ส่งต่อสำเร็จ","Completed"),
              ref_stats[1] if ref_stats else 0)
    k5.metric("🎓 " + _t("การอบรม","Trainings"),
              len(trainings))

    st.divider()

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_info, tab_train, tab_add_train, tab_visits = st.tabs([
        "📋 " + _t("ข้อมูลส่วนตัว","Personal Info"),
        "🎓 " + _t("ประวัติการอบรม","Training History"),
        "➕ " + _t("เพิ่มการอบรม","Add Training"),
        "🏠 " + _t("การเยี่ยมบ้านล่าสุด","Recent Visits"),
    ])

    # ── Tab 1: Personal Info ──────────────────────────────────────────────────
    with tab_info:
        st.markdown("##### " + _t("ข้อมูลส่วนตัวและการติดต่อ","Personal & Contact Info"))
        i1,i2 = st.columns(2)
        with i1:
            st.markdown(f"**{_t('ชื่อ-นามสกุล','Full Name')}:** {vol.full_name}")
            st.markdown(f"**{_t('รหัส อสม.','Code')}:** `{vol.volunteer_code}`")
            st.markdown(f"**{_t('ตำแหน่ง','Position')}:** {vol.position or '—'}")
            st.markdown(f"**{_t('โทรศัพท์','Phone')}:** {vol.phone or '—'}")
            email = getattr(vol,"email",None) or "—"
            st.markdown(f"**Email:** {email}")
            line_id = getattr(vol,"line_id",None) or "—"
            st.markdown(f"**Line ID:** {line_id}")
        with i2:
            st.markdown(f"**{_t('หมู่บ้าน','Village')}:** {vol.village or '—'}")
            st.markdown(f"**{_t('ตำบล','Subdistrict')}:** {vol.subdistrict or '—'}")
            st.markdown(f"**{_t('อำเภอ','District')}:** {vol.district or '—'}")
            st.markdown(f"**{_t('จังหวัด','Province')}:** {vol.province or '—'}")
            edu = getattr(vol,"education",None) or "—"
            st.markdown(f"**{_t('การศึกษา','Education')}:** {edu}")
            start_yr = getattr(vol,"start_year",None)
            if start_yr:
                disp_yr = ad_to_be_year(int(start_yr)) if is_th else start_yr
                st.markdown(f"**{_t('เริ่มเป็น อสม. ปี','VHV Since')}:** {disp_yr}")

        notes = getattr(vol,"notes",None)
        if notes:
            st.markdown(f"**{_t('หมายเหตุ','Notes')}:** {notes}")

        # Edit extra fields inline
        st.divider()
        st.markdown("##### " + _t("แก้ไขข้อมูลเพิ่มเติม","Edit Additional Info"))
        actor = get_current_user().email if get_current_user() else "system"
        with st.form("vol_extra_edit"):
            ei1,ei2 = st.columns(2)
            e_edu     = ei1.text_input(_t("การศึกษา","Education"),
                                        value=getattr(vol,"education","") or "")
            e_line    = ei2.text_input("Line ID",
                                        value=getattr(vol,"line_id","") or "")
            # start_year — completely safe read with full clamping
            try:
                _raw_start = getattr(vol, "start_year", None)
                _raw_int   = int(_raw_start) if _raw_start is not None else None
            except Exception:
                _raw_int = None

            if _raw_int is None:
                _start_be, _start_ad = 2560, 2017
            elif _raw_int > 2400:
                # Stored as BE year (e.g. 2560)
                _start_be = _raw_int
                _start_ad = _raw_int - 543
            else:
                # Stored as AD year (e.g. 2017)
                _start_ad = _raw_int
                _start_be = _raw_int + 543

            _min_yr = 2500 if is_th else 1957
            _max_yr = 2599 if is_th else 2056
            # Always clamp before passing to number_input
            _start_display = int(max(_min_yr, min(_max_yr, _start_be if is_th else _start_ad)))
            e_start = ei1.number_input(
                _t("เริ่มเป็น อสม. ปี (พ.ศ.)", "VHV Since Year (AD)"),
                min_value=_min_yr, max_value=_max_yr,
                value=_start_display,
                step=1,
            )
            e_notes   = st.text_area(_t("หมายเหตุ","Notes"),
                                      value=getattr(vol,"notes","") or "")
            esub = st.form_submit_button(_t("💾 บันทึก","💾 Save"), type="primary")
        if esub:
            # Convert BE year back to AD for storage
            from app.shared.date_utils import be_to_ad_year
            # Always save as AD year in DB
            ad_year = be_to_ad_year(int(e_start)) if is_th else int(e_start)
            # Safety clamp: ensure it's a valid AD year
            if ad_year > 2100: ad_year = ad_year - 543
            if ad_year < 1900: ad_year = ad_year + 543
            with get_sync_db() as db:
                try:
                    db.execute(text("""
                        UPDATE volunteers SET education=:edu, line_id=:line,
                        start_year=:yr, notes=:notes, updated_by=:actor
                        WHERE id=:id
                    """), {"edu":e_edu or None,"line":e_line or None,
                           "yr":ad_year,"notes":e_notes or None,
                           "actor":actor,"id":str(volunteer_id)})
                except Exception as e:
                    st.error(str(e))
            st.success(_t("บันทึกสำเร็จ","Saved.")); st.rerun()

    # ── Tab 2: Training History ───────────────────────────────────────────────
    with tab_train:
        if trainings:
            st.markdown(f"**{_t('การอบรมทั้งหมด','Total Trainings')}: {len(trainings)} {_t('ครั้ง','sessions')}**")
            st.divider()

            total_hrs = sum(float(t[4] or 0) for t in trainings)
            h1,h2 = st.columns(2)
            h1.metric("⏱️ " + _t("ชั่วโมงอบรมรวม","Total Training Hours"),
                      f"{total_hrs:.1f} {_t('ชั่วโมง','hrs')}")
            h2.metric("📅 " + _t("อบรมล่าสุด","Latest Training"),
                      fmt_date(trainings[0][1]) if trainings else "—")

            st.divider()
            trows = []
            for tr in trainings:
                trows.append({
                    _t("วันที่","Date"):           fmt_date(tr[1]),
                    _t("หัวข้อการอบรม","Topic"):   tr[2],
                    _t("หน่วยงาน","Organizer"):    tr[3] or "—",
                    _t("ชั่วโมง","Hours"):         f"{tr[4]:.1f}" if tr[4] else "—",
                    _t("สถานที่","Location"):       tr[5] or "—",
                    _t("เลขที่ใบรับรอง","Cert No."): tr[6] or "—",
                })
            st.dataframe(pd.DataFrame(trows), use_container_width=True, hide_index=True)

            # Delete training
            st.divider()
            del_opts = {f"{fmt_date(tr[1])} — {tr[2][:40]}": str(tr[0]) for tr in trainings}
            del_sel  = st.selectbox(_t("เลือกรายการเพื่อลบ","Select to Delete"), list(del_opts.keys()))
            if st.button("🗑️ " + _t("ลบการอบรม","Delete Training"), key="del_train"):
                with get_sync_db() as db:
                    db.execute(text(
                        "UPDATE volunteer_trainings SET is_deleted=true WHERE id=:id"
                    ), {"id": del_opts[del_sel]})
                st.success(_t("ลบสำเร็จ","Deleted.")); st.rerun()
        else:
            st.info(_t("ยังไม่มีประวัติการอบรม","No training records yet."))

    # ── Tab 3: Add Training ───────────────────────────────────────────────────
    with tab_add_train:
        st.markdown("#### 🎓 " + _t("บันทึกการอบรม","Record Training"))
        actor = get_current_user().email if get_current_user() else "system"
        with st.form("add_training"):
            f1,f2 = st.columns(2)
            train_date = be_date_input(
                _t("วันที่อบรม","Training Date"),
                value=date.today(), key="train_date"
            )
            topic = f2.text_input(
                _t("หัวข้อการอบรม *","Training Topic *"),
                placeholder=_t("เช่น การดูแลผู้สูงอายุ","e.g. Elderly Care")
            )
            f3,f4 = st.columns(2)
            organizer = f3.text_input(
                _t("อบรมโดยหน่วยงาน","Organized By"),
                placeholder=_t("เช่น สสจ.เชียงใหม่","e.g. Chiang Mai PHO")
            )
            location = f4.text_input(
                _t("สถานที่อบรม","Training Location"),
                placeholder=_t("เช่น ห้องประชุมศูนย์สุขภาพ","e.g. Health Center")
            )
            f5,f6 = st.columns(2)
            duration = f5.number_input(
                _t("จำนวนชั่วโมง","Duration (hours)"),
                min_value=0.5, max_value=200.0, value=6.0, step=0.5
            )
            cert_no = f6.text_input(
                _t("เลขที่ใบรับรอง (ถ้ามี)","Certificate No. (optional)")
            )
            notes = st.text_area(_t("หมายเหตุ","Notes"))
            sub = st.form_submit_button(
                "💾 " + _t("บันทึกการอบรม","Save Training"),
                type="primary", use_container_width=True
            )

        if sub and topic:
            with get_sync_db() as db:
                db.execute(text("""
                    INSERT INTO volunteer_trainings
                        (id, volunteer_id, training_date, topic, organizer,
                         duration_hours, location, certificate_no, notes,
                         created_by, updated_by)
                    VALUES
                        (gen_random_uuid(), :vid, :dt, :topic, :org,
                         :dur, :loc, :cert, :notes, :actor, :actor)
                """), {
                    "vid":   str(volunteer_id),
                    "dt":    str(train_date),
                    "topic": topic,
                    "org":   organizer or None,
                    "dur":   duration,
                    "loc":   location or None,
                    "cert":  cert_no or None,
                    "notes": notes or None,
                    "actor": actor,
                })
            st.success(_t(
                f"✅ บันทึกการอบรม '{topic}' สำเร็จ",
                f"✅ Training '{topic}' recorded."
            ))
            st.rerun()
        elif sub:
            st.warning(_t("กรุณากรอกหัวข้อการอบรม","Training topic is required."))

    # ── Tab 4: Recent Visits ──────────────────────────────────────────────────
    with tab_visits:
        if recent_visits:
            VTYPE_TH = {"routine":"ตามแผน","follow_up":"ติดตาม",
                        "emergency":"ฉุกเฉิน","post_referral":"หลังส่งต่อ"}
            vrows = [{
                _t("วันที่","Date"):          fmt_date(v[0]),
                _t("ประชาชน","Citizen"):      v[2] or "—",
                _t("ประเภท","Type"):          VTYPE_TH.get(v[1],v[1]) if is_th else v[1],
                _t("บันทึก","Note"):          (v[3] or "")[:60],
            } for v in recent_visits]
            st.dataframe(pd.DataFrame(vrows), use_container_width=True, hide_index=True)
        else:
            st.info(_t("ยังไม่มีประวัติการเยี่ยมบ้าน","No visit history."))
