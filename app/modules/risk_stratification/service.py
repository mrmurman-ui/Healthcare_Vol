"""Risk Stratification — operational support priority scoring."""
from __future__ import annotations


def _t(th: str, en: str) -> str:
    import streamlit as _st
    return th if _st.session_state.get("lang","TH") == "TH" else en


import uuid
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import Float, String, Text, func, select
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db_sync import get_sync_db
from app.modules.auth.session import get_current_user
from app.modules.citizens.model import Citizen
from app.modules.health_profiles.model import HealthProfile
from app.modules.localization.service import t
from app.shared.base_model import UUIDBase
import sqlalchemy as sa

RISK_LEVELS = ["low", "moderate", "high", "critical"]
RISK_LABELS = {
    "low": "🟢 Low Priority",
    "moderate": "🟡 Moderate Priority",
    "high": "🟠 High Priority",
    "critical": "🔴 Critical Priority",
}
RISK_LABELS_TH = {
    "low": "🟢 ต่ำ",
    "moderate": "🟡 ปานกลาง",
    "high": "🟠 สูง",
    "critical": "🔴 วิกฤต",
}
RISK_FILTER_OPTIONS_TH = {
    "": "ทั้งหมด",
    "low": "🟢 ต่ำ",
    "moderate": "🟡 ปานกลาง",
    "high": "🟠 สูง",
    "critical": "🔴 วิกฤต",
}


# ── Model ─────────────────────────────────────────────────────────────────────

class RiskScore(UUIDBase):
    __tablename__ = "risk_scores"

    citizen_id: Mapped[uuid.UUID] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    score: Mapped[float] = mapped_column(Float, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(20), default="low")
    calculation_date: Mapped[str | None] = mapped_column(String(20))
    factors: Mapped[str | None] = mapped_column(Text)  # JSON-like text
    is_deleted: Mapped[bool] = mapped_column(default=False)


# ── Calculator ────────────────────────────────────────────────────────────────

def calculate_risk(citizen: Citizen, profile: HealthProfile | None) -> dict:
    """
    Operational support priority score (0-100).
    NOT a medical risk score. NOT a disease risk assessment.
    Factors represent community support needs only.
    """
    score = 0.0
    factors = []

    # Age
    if citizen.date_of_birth:
        try:
            age = (date.today() - citizen.date_of_birth).days // 365
            if age >= 80:
                score += 20
                factors.append("Age 80+")
            elif age >= 70:
                score += 15
                factors.append("Age 70-79")
            elif age >= 60:
                score += 10
                factors.append("Age 60-69")
        except Exception:
            pass

    if profile:
        if profile.lives_alone_profile:
            score += 15
            factors.append("Lives alone")
        if profile.is_homebound:
            score += 15
            factors.append("Homebound")
        if profile.is_bedridden_profile:
            score += 20
            factors.append("Bedridden")
        if not profile.has_caregiver:
            score += 10
            factors.append("No caregiver")
        if profile.has_social_isolation:
            score += 8
            factors.append("Social isolation")
        chronic = sum([
            profile.has_diabetes, profile.has_hypertension,
            profile.has_dyslipidemia, profile.has_heart_disease,
            profile.has_stroke, profile.has_cancer,
            profile.has_kidney_disease, profile.has_lung_disease,
        ])
        score += min(chronic * 5, 20)
        if chronic:
            factors.append(f"{chronic} chronic condition(s)")
        hazards = sum([profile.unsafe_bathroom, profile.slippery_floor,
                       profile.poor_lighting, profile.unsafe_stairs])
        if hazards:
            score += min(hazards * 3, 12)
            factors.append("Unsafe housing")
        if profile.has_income_problems:
            score += 5
            factors.append("Income problems")

    score = min(score, 100)

    if score < 25:
        level = "low"
    elif score < 50:
        level = "moderate"
    elif score < 75:
        level = "high"
    else:
        level = "critical"

    return {"score": round(score, 1), "risk_level": level, "factors": ", ".join(factors)}


def run_risk_engine(db, actor: str = "system") -> int:
    citizens = db.execute(select(Citizen).limit(2000)).scalars().all()
    updated = 0
    for citizen in citizens:
        profile = db.execute(
            select(HealthProfile).where(HealthProfile.citizen_id == citizen.id)
        ).scalar_one_or_none()
        result = calculate_risk(citizen, profile)
        existing = db.execute(
            select(RiskScore).where(RiskScore.citizen_id == str(citizen.id))
        ).scalar_one_or_none()
        if existing:
            existing.score = result["score"]
            existing.risk_level = result["risk_level"]
            existing.factors = result["factors"]
            existing.calculation_date = str(date.today())
            existing.updated_by = actor
        else:
            db.add(RiskScore(
                citizen_id=str(citizen.id),
                score=result["score"],
                risk_level=result["risk_level"],
                factors=result["factors"],
                calculation_date=str(date.today()),
                created_by=actor, updated_by=actor,
            ))
        updated += 1
    db.commit()
    return updated


# ── Page ─────────────────────────────────────────────────────────────────────

def render_risk_stratification() -> None:
    st.header("🎯 " + t("nav_risk_stratification"))
    st.caption(_t("คะแนนลำดับความสำคัญชุมชน — ไม่ใช่การประเมินความเสี่ยงทางการแพทย์", "Community support priority scores — NOT medical risk assessment."))

    col1, col2 = st.columns([3, 1])
    if col2.button("🔄 " + _t("คำนวณใหม่ทั้งหมด", "Recalculate All"), type="primary"):
        user = get_current_user()
        with get_sync_db() as db:
            count = run_risk_engine(db, user.email if user else "system")
        st.success(_t(f"คำนวณใหม่ {count} ราย", f"Recalculated {count} citizens."))
        st.rerun()

    with get_sync_db() as db:
        level_stats = db.execute(
            select(RiskScore.risk_level, func.count())
            .where(RiskScore.is_deleted == False)
            .group_by(RiskScore.risk_level)
        ).all()

        is_thai = _t("th", "en") == "th"
        if is_thai:
            filter_options = [""] + RISK_LEVELS
            filter_display = ["ทั้งหมด"] + [RISK_LABELS_TH.get(l, l) for l in RISK_LEVELS]
            filter_sel = st.selectbox(_t("กรองระดับความสำคัญ", "Filter Priority Level"), filter_display)
            level_filter = filter_options[filter_display.index(filter_sel)]
        else:
            level_filter = st.selectbox("Filter Priority Level", [""] + RISK_LEVELS)

        stmt = select(RiskScore).where(RiskScore.is_deleted == False)
        if level_filter:
            stmt = stmt.where(RiskScore.risk_level == level_filter)
        stmt = stmt.order_by(RiskScore.score.desc()).limit(200)
        scores = db.execute(stmt).scalars().all()

    stat_map = {r[0]: r[1] for r in level_stats}
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🔴 " + _t("วิกฤต", "Critical"), stat_map.get("critical", 0))
    c2.metric("🟠 " + _t("สูง", "High"), stat_map.get("high", 0))
    c3.metric("🟡 " + _t("ปานกลาง", "Moderate"), stat_map.get("moderate", 0))
    c4.metric("🟢 " + _t("ต่ำ", "Low"), stat_map.get("low", 0))

    if stat_map:
        label_map = RISK_LABELS_TH if _t("th", "en") == "th" else RISK_LABELS
        fig = px.pie(
            names=[label_map.get(k, k) for k in stat_map],
            values=list(stat_map.values()),
            title=_t("การกระจายลำดับความสำคัญการสนับสนุนชุมชน", "Community Support Priority Distribution"),
            color_discrete_map={
                label_map["critical"]: "#e63946",
                label_map["high"]: "#f4a261",
                label_map["moderate"]: "#e9c46a",
                label_map["low"]: "#2a9d8f",
            },
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    if scores:
        label_map = RISK_LABELS_TH if _t("th", "en") == "th" else RISK_LABELS
        df = pd.DataFrame([{
            _t("ระดับความสำคัญ", "Priority Level"): label_map.get(s.risk_level, s.risk_level),
            _t("คะแนน", "Score"): s.score,
            _t("ปัจจัยหลัก", "Key Factors"): (s.factors or "")[:100],
            _t("วันที่คำนวณ", "Calculated"): s.calculation_date or "",
        } for s in scores])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info(_t("ยังไม่มีคะแนน กด 'คำนวณใหม่ทั้งหมด' เพื่อสร้าง", "No scores yet. Click 'Recalculate All' to generate."))
