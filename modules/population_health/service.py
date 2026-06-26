"""Population Health Intelligence — pyramids, ratios, trends, simple forecasting."""
from __future__ import annotations


def _t(th: str, en: str) -> str:
    import streamlit as _st
    return th if _st.session_state.get("lang","TH") == "TH" else en


import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import func, select, text

from app.core.db_sync import get_sync_db
from app.modules.citizens.model import Citizen
from app.modules.health_profiles.model import HealthProfile
from app.modules.home_visits.model import HomeVisit
from app.modules.localization.service import t
from app.modules.referrals.model import Referral
from app.modules.volunteers.model import Volunteer
import sqlalchemy as sa


def simple_forecast(values: list[float], periods: int = 3) -> list[float]:
    """Simple linear extrapolation for trend forecasting. No AI diagnosis."""
    if len(values) < 2:
        return [values[-1]] * periods if values else [0.0] * periods
    n = len(values)
    x_mean = (n - 1) / 2
    y_mean = sum(values) / n
    numer = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
    denom = sum((i - x_mean) ** 2 for i in range(n))
    slope = numer / denom if denom else 0
    intercept = y_mean - slope * x_mean
    return [round(intercept + slope * (n + i), 1) for i in range(periods)]


def render_population_health() -> None:
    st.header("🌏 " + t("nav_population_health"))

    with get_sync_db() as db:
        total = db.execute(select(func.count()).select_from(Citizen)).scalar() or 0
        total_vols = db.execute(select(func.count()).select_from(Volunteer)).scalar() or 0

        cit_row = db.execute(
            select(
                func.sum(Citizen.is_elderly.cast(sa.Integer)).label("elderly"),
                func.sum(Citizen.is_disabled.cast(sa.Integer)).label("disabled"),
                func.sum(Citizen.is_bedridden.cast(sa.Integer)).label("bedridden"),
                func.sum(Citizen.is_living_alone.cast(sa.Integer)).label("alone"),
            )
        ).one()

        hp_row = db.execute(
            select(
                func.sum(HealthProfile.is_homebound.cast(sa.Integer)).label("homebound"),
                func.sum(HealthProfile.has_diabetes.cast(sa.Integer)).label("diabetes"),
                func.sum(HealthProfile.has_hypertension.cast(sa.Integer)).label("hypertension"),
                func.sum(HealthProfile.has_heart_disease.cast(sa.Integer)).label("heart"),
                func.count().label("profiles"),
            )
        ).one()

        age_rows = db.execute(text("""
            SELECT
                CASE
                    WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) < 15 THEN '0-14'
                    WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) < 30 THEN '15-29'
                    WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) < 45 THEN '30-44'
                    WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) < 60 THEN '45-59'
                    WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) < 75 THEN '60-74'
                    ELSE '75+'
                END as age_group,
                gender,
                COUNT(*) as cnt
            FROM citizens
            WHERE date_of_birth IS NOT NULL
            GROUP BY age_group, gender
            ORDER BY age_group
        """)).fetchall()

        monthly_visits = db.execute(text("""
            SELECT TO_CHAR(visit_date::date, 'YYYY-MM') as month, COUNT(*) as cnt
            FROM home_visits GROUP BY month ORDER BY month DESC LIMIT 12
        """)).fetchall()

        monthly_refs = db.execute(text("""
            SELECT TO_CHAR(referral_date::date, 'YYYY-MM') as month, COUNT(*) as cnt
            FROM referrals GROUP BY month ORDER BY month DESC LIMIT 12
        """)).fetchall()

    elderly = int(cit_row.elderly or 0)
    disabled = int(cit_row.disabled or 0)
    homebound = int(hp_row.homebound or 0)
    alone = int(cit_row.alone or 0)

    # Key ratios
    st.subheader(_t("อัตราสุขภาพประชากร","Population Health Ratios"))
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(_t("สัดส่วนผู้สูงอายุ","Elderly Ratio"), f"{round(elderly/max(total,1)*100,1)}%", f"{elderly}")
    c2.metric(_t("สัดส่วนผู้พิการ","Disabled Ratio"), f"{round(disabled/max(total,1)*100,1)}%", f"{disabled}")
    c3.metric(_t("สัดส่วนผู้ติดบ้าน","Homebound Ratio"), f"{round(homebound/max(total,1)*100,1)}%", f"{homebound}")
    c4.metric(_t("สัดส่วนอยู่คนเดียว","Living Alone Ratio"), f"{round(alone/max(total,1)*100,1)}%", f"{alone}")
    c5.metric(_t("ความครอบคลุม อสม.","Volunteer Coverage"), f"1:{round(total/max(total_vols,1),0):.0f}")

    # Dependency ratio
    youth_elderly = elderly  # simplified
    working_age = max(total - youth_elderly, 1)
    dep_ratio = round(youth_elderly / working_age * 100, 1)
    st.metric(_t("อัตราพึ่งพิงผู้สูงอายุ","Elderly Dependency Ratio"), f"{dep_ratio}%",
              help="Elderly population / working-age population × 100")

    st.divider()
    tab1, tab2, tab3, tab4 = st.tabs([
        _t("พีระมิดประชากร","Population Pyramid"), _t("การกระจายโรค","Disease Distribution"), _t("แนวโน้มบริการ","Service Trends"), _t("พยากรณ์","Forecast")
    ])

    with tab1:
        if age_rows:
            age_groups = sorted(set(r[0] for r in age_rows))
            male_counts = {r[0]: r[2] for r in age_rows if r[1] == "male"}
            female_counts = {r[0]: r[2] for r in age_rows if r[1] == "female"}

            fig = go.Figure()
            fig.add_trace(go.Bar(
                y=age_groups,
                x=[-male_counts.get(ag, 0) for ag in age_groups],
                name=_t("ชาย","Male"), orientation="h",
                marker_color="#1e3a5f",
            ))
            fig.add_trace(go.Bar(
                y=age_groups,
                x=[female_counts.get(ag, 0) for ag in age_groups],
                name=_t("หญิง","Female"), orientation="h",
                marker_color="#e63946",
            ))
            fig.update_layout(
                title=_t("พีระมิดประชากร","Population Pyramid"),
                barmode="overlay",
                xaxis_title=_t("ประชากร","Population"),
                yaxis_title=_t("กลุ่มอายุ",_t("กลุ่มอายุ","Age Group")),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(_t("กรุณาเพิ่มวันเกิดของประชาชนเพื่อดูพีระมิดประชากร", "Add citizen birth dates to see population pyramid."))

    with tab2:
        profiles_total = int(hp_row.profiles or 1)
        chronic_data = {
            _t("เบาหวาน", "Diabetes"): int(hp_row.diabetes or 0),
            _t("ความดันโลหิตสูง", "Hypertension"): int(hp_row.hypertension or 0),
            _t("โรคหัวใจ", "Heart Disease"): int(hp_row.heart or 0),
        }
        fig = px.bar(
            x=list(chronic_data.keys()),
            y=list(chronic_data.values()),
            title=_t(
                f"การกระจายโรคเรื้อรัง (จาก {profiles_total} โปรไฟล์)",
                f"Chronic Condition Distribution (from {profiles_total} profiles)"
            ),
            color_discrete_sequence=["#e63946"],
        )
        st.plotly_chart(fig, use_container_width=True)

        vulnerability = {
            _t("ติดบ้าน", "Homebound"): homebound,
            _t("ผู้พิการ", "Disabled"): disabled,
            _t("อยู่คนเดียว", "Living Alone"): alone,
            _t("ติดเตียง", "Bedridden"): int(cit_row.bedridden or 0),
        }
        fig2 = px.pie(
            names=list(vulnerability.keys()),
            values=list(vulnerability.values()),
            title=_t("การกระจายความเปราะบาง", "Vulnerability Distribution"),
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        col1, col2 = st.columns(2)
        if monthly_visits:
            months = [r[0] for r in reversed(monthly_visits)]
            counts = [r[1] for r in reversed(monthly_visits)]
            fig = px.line(x=months, y=counts,
                          title=_t("แนวโน้มการเยี่ยมบ้าน", "Home Visit Trend"),
                          markers=True, color_discrete_sequence=["#1e3a5f"])
            col1.plotly_chart(fig, use_container_width=True)

        if monthly_refs:
            months2 = [r[0] for r in reversed(monthly_refs)]
            counts2 = [r[1] for r in reversed(monthly_refs)]
            fig2 = px.line(x=months2, y=counts2,
                           title=_t("แนวโน้มการส่งต่อ", "Referral Trend"),
                           markers=True, color_discrete_sequence=["#e63946"])
            col2.plotly_chart(fig2, use_container_width=True)

    with tab4:
        st.subheader(_t("พยากรณ์แนวโน้มอย่างง่าย","Simple Trend Forecast"))
        st.caption(_t("การพยากรณ์เชิงเส้นตรง — ไม่ใช่การวินิจฉัย AI","Linear extrapolation only — not AI diagnosis, not clinical prediction."))

        if monthly_visits and len(monthly_visits) >= 3:
            visit_vals = [r[1] for r in reversed(monthly_visits)]
            forecast = simple_forecast(visit_vals, 3)
            all_labels = [r[0] for r in reversed(monthly_visits)] + [
                f"Forecast+{i+1}" for i in range(3)
            ]
            all_vals = visit_vals + forecast
            colors = ["#1e3a5f"] * len(visit_vals) + ["#e9c46a"] * 3

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=all_labels[:len(visit_vals)], y=all_vals[:len(visit_vals)],
                name=_t("ข้อมูลจริง","Actual"), line=dict(color="#1e3a5f"),
            ))
            fig.add_trace(go.Scatter(
                x=all_labels[len(visit_vals)-1:], y=all_vals[len(visit_vals)-1:],
                name=_t("พยากรณ์","Forecast"), line=dict(color="#e9c46a", dash="dash"),
            ))
            fig.update_layout(title=_t(
                "การพยากรณ์ความต้องการเยี่ยมบ้าน (3 ช่วง)",
                "Home Visit Demand Forecast (3 periods)"
            ))
            st.plotly_chart(fig, use_container_width=True)

            col1, col2, col3 = st.columns(3)
            col1.metric(_t("ช่วงพยากรณ์ที่ 1", "Forecast Period 1"), forecast[0])
            col2.metric(_t("ช่วงพยากรณ์ที่ 2", "Forecast Period 2"), forecast[1])
            col3.metric(_t("ช่วงพยากรณ์ที่ 3", "Forecast Period 3"), forecast[2])
        else:
            st.info(_t("ต้องการข้อมูลอย่างน้อย 3 เดือนเพื่อสร้างการพยากรณ์", "Need at least 3 months of data to generate forecast."))
