# -*- coding: utf-8 -*-
"""Dashboard data service — cached queries + bilingual AI summary."""
from __future__ import annotations

import streamlit as st
from datetime import date, timedelta
from sqlalchemy import func, select, text
import sqlalchemy as sa


@st.cache_data(ttl=120, show_spinner=False)
def load_all_dashboard_data() -> dict:
    data = {
        "population": {}, "chronic": {}, "alerts": {},
        "visits": {}, "referrals": {}, "tasks": {},
        "volunteers": {}, "scorecards": [], "gis": [],
        "age_groups": [], "trends": {}, "assessments": {},
    }
    try:
        from app.core.db_sync import get_sync_db
        from app.modules.citizens.model import Citizen
        from app.modules.early_warning.model import EarlyWarning
        from app.modules.health_assessments.model import HealthAssessment
        from app.modules.health_profiles.model import HealthProfile
        from app.modules.home_visits.model import HomeVisit
        from app.modules.referrals.model import Referral
        from app.modules.tasks.model import Task
        from app.modules.volunteers.model import Volunteer

        with get_sync_db() as db:
            # Population — use raw SQL to handle extra columns added via ALTER TABLE
            try:
                pop_row = db.execute(text("""
                    SELECT
                        COUNT(*)                                                    AS total,
                        SUM(CASE WHEN is_elderly    = true THEN 1 ELSE 0 END)      AS elderly,
                        SUM(CASE WHEN is_disabled   = true THEN 1 ELSE 0 END)      AS disabled,
                        SUM(CASE WHEN is_bedridden  = true THEN 1 ELSE 0 END)      AS bedridden,
                        SUM(CASE WHEN is_living_alone = true THEN 1 ELSE 0 END)    AS alone,
                        SUM(CASE WHEN is_pregnant   = true THEN 1 ELSE 0 END)      AS pregnant
                    FROM citizens
                    WHERE is_deleted IS NULL OR is_deleted = false
                """)).fetchone()
                data["population"] = {
                    "total":       int(pop_row[0] or 0),
                    "elderly":     int(pop_row[1] or 0),
                    "disabled":    int(pop_row[2] or 0),
                    "bedridden":   int(pop_row[3] or 0),
                    "living_alone":int(pop_row[4] or 0),
                    "pregnant":    int(pop_row[5] or 0),
                }
            except Exception as _e:
                # Fallback: at least get total count
                try:
                    total_c = db.execute(text("SELECT COUNT(*) FROM citizens WHERE is_deleted IS NULL OR is_deleted=false")).scalar() or 0
                    elderly_c = db.execute(text("SELECT COUNT(*) FROM citizens WHERE is_elderly=true AND (is_deleted IS NULL OR is_deleted=false)")).scalar() or 0
                    disabled_c = db.execute(text("SELECT COUNT(*) FROM citizens WHERE is_disabled=true AND (is_deleted IS NULL OR is_deleted=false)")).scalar() or 0
                    bedridden_c = db.execute(text("SELECT COUNT(*) FROM citizens WHERE is_bedridden=true AND (is_deleted IS NULL OR is_deleted=false)")).scalar() or 0
                    data["population"] = {
                        "total": total_c, "elderly": elderly_c,
                        "disabled": disabled_c, "bedridden": bedridden_c,
                        "living_alone": 0, "pregnant": 0,
                    }
                except Exception:
                    pass

            # Age groups
            try:
                rows = db.execute(text("""
                    SELECT
                        CASE
                            WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) BETWEEN 0 AND 14 THEN '0-14'
                            WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) BETWEEN 15 AND 24 THEN '15-24'
                            WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) BETWEEN 25 AND 44 THEN '25-44'
                            WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) BETWEEN 45 AND 59 THEN '45-59'
                            WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) BETWEEN 60 AND 69 THEN '60-69'
                            WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) BETWEEN 70 AND 79 THEN '70-79'
                            ELSE '80+'
                        END as grp, gender, COUNT(*) as cnt
                    FROM citizens
                    WHERE date_of_birth IS NOT NULL
                      AND (is_deleted IS NULL OR is_deleted = false)
                    GROUP BY grp, gender
                """)).fetchall()
                data["age_groups"] = [{"group": r[0], "gender": r[1] or "other", "count": r[2]}
                                       for r in rows]
            except Exception:
                pass

            # Chronic
            try:
                hp = db.execute(select(
                    func.count().label("tot"),
                    func.sum(HealthProfile.has_diabetes.cast(sa.Integer)).label("dm"),
                    func.sum(HealthProfile.has_hypertension.cast(sa.Integer)).label("ht"),
                    func.sum(HealthProfile.has_dyslipidemia.cast(sa.Integer)).label("dl"),
                    func.sum(HealthProfile.has_heart_disease.cast(sa.Integer)).label("hd"),
                    func.sum(HealthProfile.has_stroke.cast(sa.Integer)).label("st"),
                    func.sum(HealthProfile.has_cancer.cast(sa.Integer)).label("ca"),
                    func.sum(HealthProfile.has_kidney_disease.cast(sa.Integer)).label("ckd"),
                    func.sum(HealthProfile.has_lung_disease.cast(sa.Integer)).label("lung"),
                    func.sum(HealthProfile.is_homebound.cast(sa.Integer)).label("hb"),
                    func.sum(HealthProfile.has_social_isolation.cast(sa.Integer)).label("si"),
                    func.sum(HealthProfile.has_income_problems.cast(sa.Integer)).label("ip"),
                )).one()
                data["chronic"] = {
                    "profiles": int(hp.tot or 0),
                    "diabetes": int(hp.dm or 0), "hypertension": int(hp.ht or 0),
                    "dyslipidemia": int(hp.dl or 0), "heart_disease": int(hp.hd or 0),
                    "stroke": int(hp.st or 0), "cancer": int(hp.ca or 0),
                    "kidney": int(hp.ckd or 0), "lung": int(hp.lung or 0),
                    "homebound": int(hp.hb or 0), "social_isolation": int(hp.si or 0),
                    "income_problems": int(hp.ip or 0),
                }
            except Exception:
                pass

            # Visits
            try:
                data["visits"]["total"] = db.execute(
                    select(func.count()).select_from(HomeVisit)
                ).scalar() or 0
                data["visits"]["last_30d"] = db.execute(text(
                    "SELECT COUNT(*) FROM home_visits WHERE visit_date::date >= CURRENT_DATE - 30"
                )).scalar() or 0
                monthly = db.execute(text("""
                    SELECT TO_CHAR(visit_date::date,'YYYY-MM') m, COUNT(*) c
                    FROM home_visits GROUP BY m ORDER BY m DESC LIMIT 12
                """)).fetchall()
                data["visits"]["monthly"] = [{"month": r[0], "count": r[1]}
                                              for r in reversed(monthly)]
            except Exception:
                pass

            # Referrals
            try:
                data["referrals"]["total"] = db.execute(
                    select(func.count()).select_from(Referral)
                ).scalar() or 0
                ref_status = db.execute(
                    select(Referral.status, func.count()).group_by(Referral.status)
                ).all()
                data["referrals"]["by_status"] = {r[0]: r[1] for r in ref_status}
                completed = data["referrals"]["by_status"].get("completed", 0)
                data["referrals"]["completion_rate"] = round(
                    completed / max(data["referrals"]["total"], 1) * 100, 1
                )
                ref_monthly = db.execute(text("""
                    SELECT TO_CHAR(referral_date::date,'YYYY-MM') m, COUNT(*) c
                    FROM referrals GROUP BY m ORDER BY m DESC LIMIT 12
                """)).fetchall()
                data["referrals"]["monthly"] = [{"month": r[0], "count": r[1]}
                                                 for r in reversed(ref_monthly)]
            except Exception:
                pass

            # Alerts
            try:
                alert_rows = db.execute(
                    select(EarlyWarning.severity, func.count())
                    .where(EarlyWarning.is_deleted == False, EarlyWarning.status == "open")
                    .group_by(EarlyWarning.severity)
                ).all()
                data["alerts"] = {r[0]: r[1] for r in alert_rows}
                data["alerts"]["total_open"] = sum(data["alerts"].values())
            except Exception:
                pass

            # Tasks
            try:
                task_rows = db.execute(text("""
                    SELECT status, COUNT(*) FROM tasks
                    WHERE is_deleted IS NULL OR is_deleted = false
                    GROUP BY status
                """)).fetchall()
                data["tasks"] = {r[0]: r[1] for r in task_rows}
                data["tasks"]["total"] = sum(data["tasks"].values())
            except Exception:
                pass

            # Volunteers
            try:
                vol_rows = db.execute(
                    select(Volunteer.status, func.count()).group_by(Volunteer.status)
                ).all()
                data["volunteers"] = {r[0]: r[1] for r in vol_rows}
                data["volunteers"]["active"] = data["volunteers"].get("active", 0)
                pop_total = data["population"].get("total", 1)
                active_vols = data["volunteers"]["active"]
                data["volunteers"]["coverage_ratio"] = round(
                    pop_total / max(active_vols, 1), 1
                )
                top_vols = db.execute(text("""
                    SELECT v.full_name, COUNT(hv.id) visits
                    FROM volunteers v LEFT JOIN home_visits hv ON hv.volunteer_id = v.id
                    GROUP BY v.id, v.full_name ORDER BY visits DESC LIMIT 10
                """)).fetchall()
                data["volunteers"]["top"] = [{"name": r[0], "visits": r[1]} for r in top_vols]
            except Exception:
                pass

            # Assessments
            try:
                data["assessments"]["total"] = db.execute(
                    select(func.count()).select_from(HealthAssessment)
                    .where(HealthAssessment.is_deleted == False)
                ).scalar() or 0
                assess_monthly = db.execute(text("""
                    SELECT TO_CHAR(assessment_date::date,'YYYY-MM') m, COUNT(*) c
                    FROM health_assessments WHERE is_deleted=false
                    GROUP BY m ORDER BY m DESC LIMIT 12
                """)).fetchall()
                data["assessments"]["monthly"] = [{"month": r[0], "count": r[1]}
                                                   for r in reversed(assess_monthly)]
            except Exception:
                pass

            # Scorecards
            try:
                from app.modules.community_scorecards.service import CommunityScorecard
                scs = db.execute(
                    select(CommunityScorecard)
                    .where(CommunityScorecard.is_deleted == False)
                    .order_by(CommunityScorecard.overall_score.desc())
                    .limit(20)
                ).scalars().all()
                data["scorecards"] = [
                    {"name": s.community_name, "district": s.district or "",
                     "score": s.overall_score or 0, "coverage": s.coverage_rate or 0,
                     "visits": s.home_visit_rate or 0,
                     "referrals": s.referral_completion_rate or 0}
                    for s in scs
                ]
            except Exception:
                pass

            # GIS
            try:
                gis_rows = db.execute(text("""
                    SELECT h.latitude, h.longitude, h.community,
                           COUNT(c.id) pop,
                           SUM(CASE WHEN c.is_elderly THEN 1 ELSE 0 END) elderly,
                           SUM(CASE WHEN c.is_disabled THEN 1 ELSE 0 END) disabled,
                           SUM(CASE WHEN c.is_bedridden THEN 1 ELSE 0 END) bedridden
                    FROM households h
                    LEFT JOIN citizens c ON c.household_id = h.id
                    WHERE h.latitude IS NOT NULL AND h.longitude IS NOT NULL
                    GROUP BY h.id, h.latitude, h.longitude, h.community
                    LIMIT 500
                """)).fetchall()
                data["gis"] = [
                    {"lat": r[0], "lon": r[1], "community": r[2] or "Unknown",
                     "pop": r[3] or 0, "elderly": r[4] or 0,
                     "disabled": r[5] or 0, "bedridden": r[6] or 0}
                    for r in gis_rows if r[0] and r[1]
                ]
            except Exception:
                pass

    except Exception:
        pass
    return data


def forecast_simple(values: list[float], periods: int = 6) -> list[float]:
    if len(values) < 2:
        return [float(values[-1] if values else 0)] * periods
    n = len(values)
    xm = (n - 1) / 2
    ym = sum(values) / n
    num = sum((i - xm) * (v - ym) for i, v in enumerate(values))
    den = sum((i - xm) ** 2 for i in range(n))
    slope = num / den if den else 0
    intercept = ym - slope * xm
    return [max(0, round(intercept + slope * (n + i), 1)) for i in range(periods)]


def generate_ai_summary(data: dict, period: str = "monthly") -> str:
    """Generate executive summary — Thai or English based on session language."""
    is_thai = st.session_state.get("lang", "TH") == "TH"

    pop   = data.get("population", {})
    chron = data.get("chronic", {})
    alrt  = data.get("alerts", {})
    vis   = data.get("visits", {})
    refs  = data.get("referrals", {})
    vols  = data.get("volunteers", {})

    total      = pop.get("total", 0)
    elderly    = pop.get("elderly", 0)
    elderly_pct = round(elderly / max(total, 1) * 100, 1)
    critical   = alrt.get("critical", 0)
    high       = alrt.get("high", 0)
    open_alrt  = alrt.get("total_open", 0)
    active_vol = vols.get("active", 0)
    coverage   = vols.get("coverage_ratio", 0)
    ref_rate   = refs.get("completion_rate", 0)
    visits_30d = vis.get("last_30d", 0)
    dm         = chron.get("diabetes", 0)
    ht         = chron.get("hypertension", 0)
    profiles   = chron.get("profiles", 0)

    today = date.today()

    if is_thai:
        # Thai months
        TH_MONTHS = ["ม.ค.","ก.พ.","มี.ค.","เม.ย.","พ.ค.","มิ.ย.",
                     "ก.ค.","ส.ค.","ก.ย.","ต.ค.","พ.ย.","ธ.ค."]
        period_map = {"monthly": "รายเดือน", "weekly": "รายสัปดาห์", "daily": "รายวัน"}
        period_th  = period_map.get(period, "รายเดือน")
        date_str   = f"{today.day} {TH_MONTHS[today.month-1]} {today.year + 543}"

        lines = [
            f"📊 **สรุปผู้บริหาร {period_th}** — จัดทำวันที่ {date_str}",
            "",
            f"**ภาพรวมประชากร:** แพลตฟอร์มกำลังติดตาม **{total:,} ประชาชน** ในชุมชน "
            f"ประชากรผู้สูงอายุ (60 ปีขึ้นไป) คิดเป็น **{elderly_pct}%** (จำนวน {elderly:,} คน)",
        ]

        if profiles > 0:
            lines.append(
                f"**ข้อมูลโปรไฟล์สุขภาพ:** มีโปรไฟล์สุขภาพทั้งหมด {profiles:,} ราย "
                f"โรคที่พบบ่อยได้แก่ ความดันโลหิตสูง ({ht:,} ราย) และเบาหวาน ({dm:,} ราย)"
            )

        lines.append(
            f"**กิจกรรมปฏิบัติการ:** มีการ **เยี่ยมบ้านจำนวน {visits_30d:,} ครั้ง** "
            f"ใน 30 วันที่ผ่านมา อัตราการส่งต่อสำเร็จอยู่ที่ **{ref_rate}%** (เป้าหมาย: 80%)"
        )

        if open_alrt > 0:
            sev_note = ""
            if critical + high > 0:
                sev_note = f" รวมถึงการแจ้งเตือนระดับวิกฤต {critical} รายการ และระดับสูง {high} รายการ"
            lines.append(
                f"**สถานะการแจ้งเตือน:** มี **{open_alrt} การแจ้งเตือนที่เปิดอยู่**"
                f"{sev_note} กรุณาดำเนินการโดยเร็ว"
            )

        lines.append(
            f"**การปฏิบัติงานอาสาสมัคร:** มี **อสม. ที่ใช้งาน {active_vol} คน** "
            f"ดูแลชุมชน อัตราส่วนประชาชนต่อ อสม. อยู่ที่ **{coverage:.1f}:1**"
        )

        recs = []
        if ref_rate < 80:
            recs.append(f"อัตราการส่งต่อสำเร็จ ({ref_rate}%) ต่ำกว่าเป้าหมาย 80% — ทบทวนกระบวนการติดตาม")
        if critical > 0:
            recs.append(f"มีการแจ้งเตือนระดับวิกฤต {critical} รายการที่ยังเปิดอยู่ — ต้องดำเนินการทันที")
        if elderly_pct > 25:
            recs.append(f"สัดส่วนผู้สูงอายุ ({elderly_pct}%) สูง — พิจารณาขยายขีดความสามารถการดูแลผู้สูงอายุ")
        if coverage > 100:
            recs.append(f"อัตราส่วนประชาชนต่อ อสม. ({coverage:.0f}:1) สูง — พิจารณาเพิ่มจำนวน อสม.")

        if recs:
            lines += ["", "**การดำเนินการที่แนะนำ:**"]
            for r in recs:
                lines.append(f"• {r}")

        lines += [
            "",
            "*รายงานนี้ครอบคลุมเฉพาะข้อมูลการปฏิบัติงานด้านสุขภาพชุมชน "
            "ไม่ถือเป็นคำแนะนำทางการแพทย์หรือการวินิจฉัยโรคแต่อย่างใด*"
        ]

    else:
        date_str = today.strftime("%d %B %Y")
        period_map = {"monthly": "Monthly", "weekly": "Weekly", "daily": "Daily"}
        period_en = period_map.get(period, "Monthly")

        lines = [
            f"📊 **{period_en} Executive Summary** — Generated {date_str}",
            "",
            f"**Population Overview:** The platform is monitoring **{total:,} citizens** "
            f"across the community. Elderly population (60+) accounts for **{elderly_pct}%** "
            f"({elderly:,} persons).",
        ]

        if profiles > 0:
            lines.append(
                f"**Health Profile Snapshot:** {profiles:,} citizens have health profiles recorded. "
                f"Top reported conditions: Hypertension ({ht:,}), Diabetes ({dm:,})."
            )

        lines.append(
            f"**Operational Activity:** **{visits_30d:,} home visits** were completed "
            f"in the last 30 days. Referral completion rate stands at **{ref_rate}%** (target: 80%)."
        )

        if open_alrt > 0:
            sev_note = ""
            if critical + high > 0:
                sev_note = f", including {critical} critical and {high} high-priority alerts"
            lines.append(
                f"**Alert Status:** **{open_alrt} open alerts** require attention{sev_note}. "
                "Prompt follow-up recommended."
            )

        lines.append(
            f"**Volunteer Operations:** **{active_vol} active volunteers** are covering the community. "
            f"Current population-to-volunteer ratio is **{coverage:.1f}:1**."
        )

        recs = []
        if ref_rate < 80:
            recs.append(f"Referral completion ({ref_rate}%) is below 80% target — review follow-up workflow")
        if critical > 0:
            recs.append(f"{critical} critical alerts are open — immediate coordinator review needed")
        if elderly_pct > 25:
            recs.append(f"Elderly ratio ({elderly_pct}%) is high — consider expanding elder care capacity")
        if coverage > 100:
            recs.append(f"Population/volunteer ratio ({coverage:.0f}:1) is high — consider volunteer recruitment")

        if recs:
            lines += ["", "**Recommended Actions:**"]
            for r in recs:
                lines.append(f"• {r}")

        lines += [
            "",
            "*This summary covers community health operations data only. "
            "It does not constitute medical advice or clinical diagnosis.*"
        ]

    return "\n".join(lines)
