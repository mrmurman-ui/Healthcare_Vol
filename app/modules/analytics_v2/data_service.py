"""Analytics data service — cached queries for all analytics modules."""
from __future__ import annotations

import streamlit as st
from datetime import date, timedelta
from sqlalchemy import func, select, text

from app.core.db_sync import get_sync_db
import sqlalchemy as sa


@st.cache_data(ttl=300, show_spinner=False)
def load_population_stats() -> dict:
    out = {
        "total": 0, "elderly": 0, "disabled": 0, "bedridden": 0,
        "living_alone": 0, "pregnant": 0,
        "age_groups": {}, "gender": {},
        "households": 0,
    }
    try:
        with get_sync_db() as db:
            from app.modules.citizens.model import Citizen
            from app.modules.households.model import Household

            row = db.execute(select(
                func.count().label("total"),
                func.sum(Citizen.is_elderly.cast(sa.Integer)).label("elderly"),
                func.sum(Citizen.is_disabled.cast(sa.Integer)).label("disabled"),
                func.sum(Citizen.is_bedridden.cast(sa.Integer)).label("bedridden"),
                func.sum(Citizen.is_living_alone.cast(sa.Integer)).label("alone"),
                func.sum(Citizen.is_pregnant.cast(sa.Integer)).label("pregnant"),
            )).one()
            out.update({
                "total": int(row.total or 0),
                "elderly": int(row.elderly or 0),
                "disabled": int(row.disabled or 0),
                "bedridden": int(row.bedridden or 0),
                "living_alone": int(row.alone or 0),
                "pregnant": int(row.pregnant or 0),
            })

            # Age groups
            age_rows = db.execute(text("""
                SELECT
                    CASE
                        WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) BETWEEN 0 AND 5 THEN '0-5'
                        WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) BETWEEN 6 AND 12 THEN '6-12'
                        WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) BETWEEN 13 AND 18 THEN '13-18'
                        WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) BETWEEN 19 AND 35 THEN '19-35'
                        WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) BETWEEN 36 AND 59 THEN '36-59'
                        WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) BETWEEN 60 AND 69 THEN '60-69'
                        WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) BETWEEN 70 AND 79 THEN '70-79'
                        ELSE '80+'
                    END as age_group,
                    gender,
                    COUNT(*) as cnt
                FROM citizens
                WHERE date_of_birth IS NOT NULL
                GROUP BY age_group, gender
                ORDER BY age_group
            """)).fetchall()
            for r in age_rows:
                g = r[1] or "other"
                out["age_groups"].setdefault(r[0], {})
                out["age_groups"][r[0]][g] = r[2]
                out["gender"][g] = out["gender"].get(g, 0) + r[2]

            out["households"] = db.execute(
                select(func.count()).select_from(Household)
            ).scalar() or 0

    except Exception:
        pass
    return out


@st.cache_data(ttl=300, show_spinner=False)
def load_chronic_disease_stats() -> dict:
    out = {
        "diabetes": 0, "hypertension": 0, "dyslipidemia": 0,
        "heart_disease": 0, "stroke": 0, "cancer": 0,
        "kidney_disease": 0, "lung_disease": 0, "total_profiles": 0,
    }
    try:
        with get_sync_db() as db:
            from app.modules.health_profiles.model import HealthProfile
            row = db.execute(select(
                func.count().label("total"),
                func.sum(HealthProfile.has_diabetes.cast(sa.Integer)).label("diabetes"),
                func.sum(HealthProfile.has_hypertension.cast(sa.Integer)).label("hypertension"),
                func.sum(HealthProfile.has_dyslipidemia.cast(sa.Integer)).label("dyslipidemia"),
                func.sum(HealthProfile.has_heart_disease.cast(sa.Integer)).label("heart"),
                func.sum(HealthProfile.has_stroke.cast(sa.Integer)).label("stroke"),
                func.sum(HealthProfile.has_cancer.cast(sa.Integer)).label("cancer"),
                func.sum(HealthProfile.has_kidney_disease.cast(sa.Integer)).label("kidney"),
                func.sum(HealthProfile.has_lung_disease.cast(sa.Integer)).label("lung"),
            )).one()
            out.update({
                "total_profiles": int(row.total or 0),
                "diabetes": int(row.diabetes or 0),
                "hypertension": int(row.hypertension or 0),
                "dyslipidemia": int(row.dyslipidemia or 0),
                "heart_disease": int(row.heart or 0),
                "stroke": int(row.stroke or 0),
                "cancer": int(row.cancer or 0),
                "kidney_disease": int(row.kidney or 0),
                "lung_disease": int(row.lung or 0),
            })
    except Exception:
        pass
    return out


@st.cache_data(ttl=300, show_spinner=False)
def load_alert_stats() -> dict:
    out = {"open": 0, "acknowledged": 0, "resolved": 0,
           "critical": 0, "high": 0, "medium": 0, "low": 0,
           "by_type": {}, "trend": []}
    try:
        with get_sync_db() as db:
            from app.modules.early_warning.model import EarlyWarning
            status_rows = db.execute(
                select(EarlyWarning.status, func.count())
                .where(EarlyWarning.is_deleted == False)
                .group_by(EarlyWarning.status)
            ).all()
            for r in status_rows:
                out[r[0]] = r[1]

            sev_rows = db.execute(
                select(EarlyWarning.severity, func.count())
                .where(EarlyWarning.is_deleted == False, EarlyWarning.status == "open")
                .group_by(EarlyWarning.severity)
            ).all()
            for r in sev_rows:
                out[r[0]] = r[1]

            type_rows = db.execute(
                select(EarlyWarning.alert_type, func.count())
                .where(EarlyWarning.is_deleted == False)
                .group_by(EarlyWarning.alert_type)
            ).all()
            out["by_type"] = {r[0]: r[1] for r in type_rows}

            trend = db.execute(text("""
                SELECT TO_CHAR(created_at, 'YYYY-MM') as month, COUNT(*) as cnt
                FROM early_warnings WHERE is_deleted = false
                GROUP BY month ORDER BY month DESC LIMIT 6
            """)).fetchall()
            out["trend"] = [{"month": r[0], "count": r[1]} for r in reversed(trend)]
    except Exception:
        pass
    return out


@st.cache_data(ttl=300, show_spinner=False)
def load_visit_stats() -> dict:
    out = {"total": 0, "last_30d": 0, "by_type": {}, "monthly_trend": [],
           "vol_productivity": []}
    try:
        with get_sync_db() as db:
            from app.modules.home_visits.model import HomeVisit
            from app.modules.volunteers.model import Volunteer
            out["total"] = db.execute(
                select(func.count()).select_from(HomeVisit)
            ).scalar() or 0
            out["last_30d"] = db.execute(text("""
                SELECT COUNT(*) FROM home_visits
                WHERE visit_date::date >= CURRENT_DATE - INTERVAL '30 days'
            """)).scalar() or 0

            type_rows = db.execute(
                select(HomeVisit.visit_type, func.count())
                .group_by(HomeVisit.visit_type)
            ).all()
            out["by_type"] = {r[0]: r[1] for r in type_rows}

            trend = db.execute(text("""
                SELECT TO_CHAR(visit_date::date, 'YYYY-MM') as month, COUNT(*) as cnt
                FROM home_visits GROUP BY month ORDER BY month DESC LIMIT 12
            """)).fetchall()
            out["monthly_trend"] = [{"month": r[0], "count": r[1]} for r in reversed(trend)]

            vol_prod = db.execute(text("""
                SELECT v.full_name, COUNT(hv.id) as visits
                FROM volunteers v
                LEFT JOIN home_visits hv ON hv.volunteer_id = v.id
                GROUP BY v.id, v.full_name
                ORDER BY visits DESC LIMIT 10
            """)).fetchall()
            out["vol_productivity"] = [{"name": r[0], "visits": r[1]} for r in vol_prod]
    except Exception:
        pass
    return out


@st.cache_data(ttl=300, show_spinner=False)
def load_referral_stats() -> dict:
    out = {"total": 0, "by_status": {}, "by_target": {}, "completion_rate": 0}
    try:
        with get_sync_db() as db:
            from app.modules.referrals.model import Referral
            out["total"] = db.execute(
                select(func.count()).select_from(Referral)
            ).scalar() or 0

            status_rows = db.execute(
                select(Referral.status, func.count()).group_by(Referral.status)
            ).all()
            out["by_status"] = {r[0]: r[1] for r in status_rows}

            target_rows = db.execute(
                select(Referral.target, func.count()).group_by(Referral.target)
            ).all()
            out["by_target"] = {str(r[0]): r[1] for r in target_rows}

            completed = out["by_status"].get("completed", 0)
            out["completion_rate"] = round(completed / max(out["total"], 1) * 100, 1)
    except Exception:
        pass
    return out


@st.cache_data(ttl=300, show_spinner=False)
def load_risk_stats() -> dict:
    out = {"critical": 0, "high": 0, "moderate": 0, "low": 0, "top_citizens": []}
    try:
        with get_sync_db() as db:
            from app.modules.risk_stratification.service import RiskScore
            from app.modules.citizens.model import Citizen
            rows = db.execute(
                select(RiskScore.risk_level, func.count())
                .where(RiskScore.is_deleted == False)
                .group_by(RiskScore.risk_level)
            ).all()
            for r in rows:
                out[r[0]] = r[1]

            top = db.execute(text("""
                SELECT c.full_name, rs.score, rs.risk_level, rs.factors
                FROM risk_scores rs
                JOIN citizens c ON c.id::text = rs.citizen_id
                WHERE rs.is_deleted = false
                ORDER BY rs.score DESC LIMIT 10
            """)).fetchall()
            out["top_citizens"] = [
                {"name": r[0], "score": r[1], "level": r[2], "factors": r[3]}
                for r in top
            ]
    except Exception:
        pass
    return out


@st.cache_data(ttl=300, show_spinner=False)
def load_gis_data() -> list:
    """Load household GPS data for GIS maps."""
    try:
        with get_sync_db() as db:
            rows = db.execute(text("""
                SELECT h.latitude, h.longitude, h.community,
                       COUNT(c.id) as pop,
                       SUM(CASE WHEN c.is_elderly THEN 1 ELSE 0 END) as elderly,
                       SUM(CASE WHEN c.is_disabled THEN 1 ELSE 0 END) as disabled,
                       SUM(CASE WHEN c.is_bedridden THEN 1 ELSE 0 END) as bedridden
                FROM households h
                LEFT JOIN citizens c ON c.household_id = h.id
                WHERE h.latitude IS NOT NULL AND h.longitude IS NOT NULL
                GROUP BY h.id, h.latitude, h.longitude, h.community
                LIMIT 500
            """)).fetchall()
            return [
                {"lat": r[0], "lon": r[1], "community": r[2] or "Unknown",
                 "pop": r[3] or 0, "elderly": r[4] or 0,
                 "disabled": r[5] or 0, "bedridden": r[6] or 0}
                for r in rows if r[0] and r[1]
            ]
    except Exception:
        return []


def _t(th: str, en: str) -> str:
    import streamlit as _st
    return th if _st.session_state.get("lang", "TH") == "TH" else en


def generate_insights(pop: dict, chronic: dict, alerts: dict,
                      visits: dict, refs: dict, risk: dict) -> list[dict]:
    """Generate automatic executive insights."""
    insights = []

    # Population insights
    if pop["total"] > 0:
        elderly_pct = round(pop["elderly"] / pop["total"] * 100, 1)
        if elderly_pct > 20:
            insights.append({
                "type": "warning", "icon": "⚠️",
                "title": _t("แจ้งเตือน: ประชากรสูงอายุ", "Aging Population Alert"),
                "text": _t(
                    f"ประชากรผู้สูงอายุคิดเป็น {elderly_pct}% ของทั้งหมด — เกินเกณฑ์ 20% ต้องเพิ่มศักยภาพด้านการดูแล",
                    f"Elderly population is {elderly_pct}% of total — above 20% threshold. Increased care capacity needed.",
                ),
            })
        if pop["bedridden"] > 0:
            insights.append({
                "type": "critical", "icon": "🚨",
                "title": _t("ประชาชนติดเตียงต้องการการดูแลเร่งด่วน", "Bedridden Citizens Require Priority"),
                "text": _t(
                    f"พบประชาชนติดเตียง {pop['bedridden']} คน แนะนำให้จัดทำโปรโตคอลติดตามรายวัน",
                    f"{pop['bedridden']} bedridden citizens identified. Recommend daily monitoring protocol.",
                ),
            })
        if pop["living_alone"] > 50:
            insights.append({
                "type": "warning", "icon": "⚠️",
                "title": _t("ความเสี่ยงการโดดเดี่ยวทางสังคม", "Social Isolation Risk"),
                "text": _t(
                    f"มีประชาชน {pop['living_alone']} คนอาศัยอยู่คนเดียว — ความเสี่ยงการโดดเดี่ยวทางสังคมสูงขึ้น",
                    f"{pop['living_alone']} citizens living alone — social isolation risk elevated.",
                ),
            })

    # Chronic disease
    total_chronic = chronic.get("total_profiles", 1)
    dm_rate = round(chronic["diabetes"] / max(total_chronic, 1) * 100, 1)
    ht_rate = round(chronic["hypertension"] / max(total_chronic, 1) * 100, 1)
    if dm_rate > 25:
        insights.append({
            "type": "warning", "icon": "📊",
            "title": _t("ความชุกของเบาหวานสูง", "High Diabetes Prevalence"),
            "text": _t(
                f"เบาหวานพบใน {dm_rate}% ของประชาชนที่มีโปรไฟล์ แนะนำให้จัดโปรแกรมตรวจคัดกรองและติดตาม",
                f"Diabetes affects {dm_rate}% of profiled citizens. Screening and monitoring program recommended.",
            ),
        })
    if ht_rate > 30:
        insights.append({
            "type": "warning", "icon": "📊",
            "title": _t("ภาระโรคความดันโลหิตสูง", "Hypertension Burden Elevated"),
            "text": _t(
                f"ความดันโลหิตสูงพบที่ {ht_rate}% — โรคเรื้อรังอันดับ 1 แนะนำให้เพิ่มการตรวจวัดความดันโลหิต",
                f"Hypertension at {ht_rate}% — top chronic disease. Blood pressure monitoring ramp-up advised.",
            ),
        })

    # Alerts
    open_alerts = alerts.get("open", 0)
    critical_alerts = alerts.get("critical", 0)
    if critical_alerts > 0:
        insights.append({
            "type": "critical", "icon": "🚨",
            "title": _t(f"การแจ้งเตือนวิกฤต {critical_alerts} รายการต้องดำเนินการทันที",
                        f"{critical_alerts} Critical Alerts Require Immediate Action"),
            "text": _t(
                "มีการแจ้งเตือนระดับวิกฤตที่ยังเปิดอยู่ แนะนำให้รายงานต่อเจ้าหน้าที่สาธารณสุขอำเภอ",
                "Critical-level alerts are open. Escalation to district health officer recommended.",
            ),
        })
    if open_alerts > 20:
        insights.append({
            "type": "warning", "icon": "⚠️",
            "title": _t("ตรวจพบการสะสมของการแจ้งเตือน", "Alert Backlog Detected"),
            "text": _t(
                f"มีการแจ้งเตือนที่เปิดอยู่ {open_alerts} รายการ — พิจารณาเพิ่มขีดความสามารถการตอบสนองของอาสาสมัคร",
                f"{open_alerts} open alerts — consider increasing volunteer response capacity.",
            ),
        })

    # Visits
    completion_rate = refs.get("completion_rate", 0)
    if completion_rate < 70:
        insights.append({
            "type": "warning", "icon": "📋",
            "title": _t("อัตราการส่งต่อสำเร็จต่ำกว่าเป้าหมาย", "Referral Completion Below Target"),
            "text": _t(
                f"อัตราการส่งต่อสำเร็จคือ {completion_rate}% — เป้าหมายคือ 80% ต้องทบทวนโปรโตคอลการติดตาม",
                f"Referral completion rate is {completion_rate}% — target is 80%. Follow-up protocol review needed.",
            ),
        })

    # Risk
    critical_risk = risk.get("critical", 0)
    if critical_risk > 0:
        insights.append({
            "type": "critical", "icon": "🎯",
            "title": _t(f"ประชาชน {critical_risk} คนอยู่ในระดับความสำคัญวิกฤต",
                        f"{critical_risk} Citizens at Critical Support Priority"),
            "text": _t(
                "แนะนำให้จัดการเยี่ยมบ้านสนับสนุนชุมชนทันทีสำหรับประชาชนที่มีความสำคัญวิกฤต",
                "Immediate community support visits recommended for critical-priority citizens.",
            ),
        })

    # Opportunity
    insights.append({
        "type": "opportunity", "icon": "✅",
        "title": _t("การครอบคลุมของแพลตฟอร์มดีขึ้น", "Platform Coverage Improving"),
        "text": _t(
            f"แพลตฟอร์มกำลังติดตามประชาชน {pop['total']} คน และมีการเยี่ยมบ้านที่บันทึกแล้ว {visits['total']} ครั้ง สามารถดูการวิเคราะห์ครอบคลุมได้",
            f"Platform now tracking {pop['total']} citizens with {visits['total']} recorded visits. Coverage analytics available.",
        ),
    })

    return insights[:6]
