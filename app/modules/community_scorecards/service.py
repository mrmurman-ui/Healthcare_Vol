"""Community Scorecards — monthly performance rankings."""
from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import Float, Integer, String, select
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db_sync import get_sync_db
from app.modules.auth.session import get_current_user
from app.modules.localization.service import t
from app.shared.date_utils import fmt_date, fmt_year, ad_to_be_year, be_to_ad_year, is_thai
from app.shared.base_model import UUIDBase


def _t(th: str, en: str) -> str:
    import streamlit as _st
    return th if _st.session_state.get("lang", "TH") == "TH" else en


# ── Model ─────────────────────────────────────────────────────────────────────

class CommunityScorecard(UUIDBase):
    __tablename__ = "community_scorecards"

    community_id: Mapped[str] = mapped_column(String(100), index=True)
    community_name: Mapped[str] = mapped_column(String(200), nullable=False)
    district: Mapped[str | None] = mapped_column(String(100))
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    population: Mapped[int | None] = mapped_column(Integer)
    coverage_rate: Mapped[float | None] = mapped_column(Float)
    assessment_rate: Mapped[float | None] = mapped_column(Float)
    home_visit_rate: Mapped[float | None] = mapped_column(Float)
    referral_completion_rate: Mapped[float | None] = mapped_column(Float)
    case_closure_rate: Mapped[float | None] = mapped_column(Float)
    volunteer_activity_rate: Mapped[float | None] = mapped_column(Float)
    overall_score: Mapped[float | None] = mapped_column(Float)
    is_deleted: Mapped[bool] = mapped_column(default=False)


def compute_overall_score(sc: CommunityScorecard) -> float:
    vals = [
        sc.coverage_rate, sc.assessment_rate, sc.home_visit_rate,
        sc.referral_completion_rate, sc.case_closure_rate, sc.volunteer_activity_rate,
    ]
    valid = [v for v in vals if v is not None]
    return round(sum(valid) / len(valid), 1) if valid else 0.0


# ── Page ─────────────────────────────────────────────────────────────────────

def render_community_scorecards() -> None:
    st.header("🏆 " + t("nav_scorecards"))

    today = date.today()
    col1, col2 = st.columns(2)
    # Year input: Thai mode shows พ.ศ., stores AD for DB
    if is_thai():
        be_year_val = ad_to_be_year(today.year)
        be_year_input = col1.number_input("ปี (พ.ศ.)", min_value=2563, max_value=2593, value=be_year_val)
        sel_year = be_to_ad_year(int(be_year_input))
    else:
        sel_year = col1.number_input("Year", min_value=2020, max_value=2050, value=today.year)
    sel_month = col2.number_input(_t("เดือน", "Month"), min_value=1, max_value=12,
                                   value=today.month)

    with get_sync_db() as db:
        scorecards = db.execute(
            select(CommunityScorecard)
            .where(
                CommunityScorecard.year == int(sel_year),
                CommunityScorecard.month == int(sel_month),
                CommunityScorecard.is_deleted == False,
            )
            .order_by(CommunityScorecard.overall_score.desc())
        ).scalars().all()

    if scorecards:
        df = pd.DataFrame([{
            _t("อันดับ", "Rank"): i + 1,
            _t("ชุมชน", "Community"): sc.community_name,
            _t("เขต", "District"): sc.district or "",
            _t("ครอบคลุม %", "Coverage %"): sc.coverage_rate or 0,
            _t("ประเมิน %", "Assessment %"): sc.assessment_rate or 0,
            _t("อัตราเยี่ยม %", "Visit Rate %"): sc.home_visit_rate or 0,
            _t("ส่งต่อ %", "Referral %"): sc.referral_completion_rate or 0,
            _t("กิจกรรม %", "Activity %"): sc.volunteer_activity_rate or 0,
            _t("คะแนนรวม", "Overall Score"): sc.overall_score or 0,
        } for i, sc in enumerate(scorecards)])

        display_year = ad_to_be_year(int(sel_year)) if is_thai() else int(sel_year)
        st.subheader(_t(f"อันดับ — {display_year}/{int(sel_month):02d}",
                        f"Rankings — {int(sel_year)}/{int(sel_month):02d}"))

        # Top 3
        col1, col2, col3 = st.columns(3)
        if len(scorecards) >= 1:
            col1.metric("🥇 " + _t("ชุมชนอันดับ 1", "Top Community"),
                        scorecards[0].community_name,
                        f"{scorecards[0].overall_score}%")
        if len(scorecards) >= 2:
            col2.metric("🥈 " + _t("อันดับ 2", "2nd"),
                        scorecards[1].community_name,
                        f"{scorecards[1].overall_score}%")
        if len(scorecards) >= 3:
            col3.metric("🥉 " + _t("อันดับ 3", "3rd"),
                        scorecards[2].community_name,
                        f"{scorecards[2].overall_score}%")

        st.dataframe(df, use_container_width=True, hide_index=True)

        score_col = _t("คะแนนรวม", "Overall Score")
        comm_col = _t("ชุมชน", "Community")
        fig = px.bar(
            df, x=comm_col, y=score_col,
            title=_t("คะแนนผลการดำเนินงานของชุมชน", "Community Performance Scores"),
            color=score_col,
            color_continuous_scale=["red", "yellow", "green"],
        )
        st.plotly_chart(fig, use_container_width=True)

        # Needs support (bottom 20%)
        threshold = df[score_col].quantile(0.2)
        needs_support = df[df[score_col] <= threshold]
        if not needs_support.empty:
            st.subheader("⚠️ " + _t("ชุมชนที่ต้องการการสนับสนุน", "Communities Needing Support"))
            st.dataframe(needs_support, use_container_width=True, hide_index=True)
    else:
        _dy = ad_to_be_year(int(sel_year)) if is_thai() else int(sel_year)
    st.info(_t(
            f"ไม่มีข้อมูลสำหรับ {_dy}/{int(sel_month):02d} กรุณาเพิ่มด้านล่าง",
            f"No scorecards for {int(sel_year)}/{int(sel_month):02d}. Add one below."
        ))

    st.divider()
    with st.expander("➕ " + _t("เพิ่มข้อมูลคะแนน", "Add Scorecard")):
        with st.form("add_scorecard"):
            col1, col2, col3 = st.columns(3)
            comm_name = col1.text_input(_t("ชื่อชุมชน", "Community Name"))
            district = col2.text_input(_t("เขต", "District"))
            population = col3.number_input(_t("ประชากร", "Population"), min_value=0, value=0)
            col4, col5, col6 = st.columns(3)
            coverage = col4.number_input(_t("อัตราครอบคลุม %", "Coverage Rate %"), 0.0, 100.0, 0.0)
            assessment = col5.number_input(_t("อัตราประเมิน %", "Assessment Rate %"), 0.0, 100.0, 0.0)
            visit_rate = col6.number_input(_t("อัตราเยี่ยมบ้าน %", "Home Visit Rate %"), 0.0, 100.0, 0.0)
            col7, col8, col9 = st.columns(3)
            ref_rate = col7.number_input(_t("อัตราส่งต่อสำเร็จ %", "Referral Completion %"), 0.0, 100.0, 0.0)
            closure = col8.number_input(_t("อัตราปิดกรณี %", "Case Closure Rate %"), 0.0, 100.0, 0.0)
            vol_rate = col9.number_input(_t("กิจกรรมอาสาสมัคร %", "Volunteer Activity %"), 0.0, 100.0, 0.0)
            submitted = st.form_submit_button(t("save"))

        if submitted and comm_name:
            user = get_current_user()
            sc = CommunityScorecard(
                community_id=comm_name.lower().replace(" ", "_"),
                community_name=comm_name, district=district,
                month=int(sel_month), year=int(sel_year),
                population=population or None,
                coverage_rate=coverage, assessment_rate=assessment,
                home_visit_rate=visit_rate, referral_completion_rate=ref_rate,
                case_closure_rate=closure, volunteer_activity_rate=vol_rate,
                created_by=user.email if user else "system",
                updated_by=user.email if user else "system",
            )
            sc.overall_score = compute_overall_score(sc)
            with get_sync_db() as db:
                db.add(sc)
            st.success(_t(
                f"บันทึกคะแนนสำเร็จ คะแนนรวม: {sc.overall_score}%",
                f"Scorecard saved. Overall: {sc.overall_score}%"
            ))
            st.rerun()
