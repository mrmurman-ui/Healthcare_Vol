"""Community Health Dashboard, Elderly Monitoring, Health Analytics."""
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
from app.modules.early_warning.model import CVIScore, EarlyWarning
from app.modules.health_assessments.model import HealthAssessment
from app.modules.health_profiles.model import HealthProfile
from app.modules.home_visits.model import HomeVisit
from app.modules.localization.service import t
from app.shared.date_utils import be_month_label, format_chart_months
from app.modules.referrals.model import Referral
from app.modules.volunteers.model import Volunteer
import sqlalchemy as sa


# ── Community Health Dashboard ────────────────────────────────────────────────

def render_community_health() -> None:
    st.header("🏘️ " + t("nav_community_health"))

    with get_sync_db() as db:
        total_citizens = db.execute(select(func.count()).select_from(Citizen)).scalar() or 0
        total_volunteers = db.execute(select(func.count()).select_from(Volunteer)).scalar() or 0
        total_visits = db.execute(select(func.count()).select_from(HomeVisit)).scalar() or 0
        total_assessments = db.execute(
            select(func.count()).select_from(HealthAssessment)
            .where(HealthAssessment.is_deleted == False)
        ).scalar() or 0
        total_referrals = db.execute(select(func.count()).select_from(Referral)).scalar() or 0

        # Vulnerability counts
        cit_row = db.execute(
            select(
                func.sum(Citizen.is_elderly.cast(sa.Integer)).label("elderly"),
                func.sum(Citizen.is_disabled.cast(sa.Integer)).label("disabled"),
                func.sum(Citizen.is_bedridden.cast(sa.Integer)).label("bedridden"),
                func.sum(Citizen.is_living_alone.cast(sa.Integer)).label("alone"),
            )
        ).one()

        # Profile-based counts
        hp_row = db.execute(
            select(
                func.sum(HealthProfile.is_homebound.cast(sa.Integer)).label("homebound"),
                func.sum(HealthProfile.has_diabetes.cast(sa.Integer)).label("diabetes"),
                func.sum(HealthProfile.has_hypertension.cast(sa.Integer)).label("hypertension"),
                func.sum(HealthProfile.has_heart_disease.cast(sa.Integer)).label("heart"),
            )
        ).one()

        # CVI distribution
        cvi_dist = db.execute(
            select(CVIScore.category, func.count()).group_by(CVIScore.category)
        ).all()

        # Open warnings
        open_warnings = db.execute(
            select(func.count()).select_from(EarlyWarning)
            .where(EarlyWarning.status == "open", EarlyWarning.is_deleted == False)
        ).scalar() or 0

        # Referral status
        ref_status = db.execute(
            select(Referral.status, func.count()).group_by(Referral.status)
        ).all()

    st.subheader(_t("ภาพรวมประชากร", "Population Overview"))
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(_t("ประชาชนทั้งหมด", "Total Citizens"), total_citizens)
    c2.metric("👴 " + _t("ผู้สูงอายุ", "Elderly"), int(cit_row.elderly or 0))
    c3.metric("♿ " + _t("ผู้พิการ", "Disabled"), int(cit_row.disabled or 0))
    c4.metric("🛏️ " + _t("ติดเตียง", "Bedridden"), int(cit_row.bedridden or 0))
    c5.metric("🏠 " + _t("อยู่คนเดียว", "Living Alone"), int(cit_row.alone or 0))

    c6, c7, c8, c9, c10 = st.columns(5)
    c6.metric(_t("อาสาสมัคร", "Volunteers"), total_volunteers)
    c7.metric(_t("การเยี่ยมบ้านทั้งหมด", "Total Visits"), total_visits)
    c8.metric(_t("การประเมิน", "Assessments"), total_assessments)
    c9.metric("⚠️ " + _t("การแจ้งเตือนที่เปิดอยู่", "Open Alerts"), open_warnings)
    c10.metric(_t("การส่งต่อ", "Referrals"), total_referrals)

    st.divider()

    # ── Section 1: Vulnerability composition ─────────────────────────────────
    st.subheader("📊 " + _t("วิเคราะห์ความเปราะบางและกลุ่มเสี่ยง",
                             "Vulnerability & Risk Analysis"))

    total = total_citizens or 1
    elderly_n  = int(cit_row.elderly  or 0)
    disabled_n = int(cit_row.disabled or 0)
    bedridden_n= int(cit_row.bedridden or 0)
    alone_n    = int(cit_row.alone    or 0)
    other_n    = max(0, total - elderly_n - disabled_n - bedridden_n - alone_n)

    VULN_COLORS = ["#F97316", "#8B5CF6", "#EF4444", "#3B82F6", "#D1D5DB"]

    col1, col2, col3 = st.columns(3)

    # Donut: population composition
    with col1:
        pie_labels = [
            _t("ผู้สูงอายุ","Elderly"),
            _t("ผู้พิการ","Disabled"),
            _t("ติดเตียง","Bedridden"),
            _t("อยู่คนเดียว","Living Alone"),
            _t("ประชากรทั่วไป","General"),
        ]
        pie_vals = [elderly_n, disabled_n, bedridden_n, alone_n, other_n]
        fig_donut = px.pie(
            names=pie_labels, values=pie_vals,
            title=_t("สัดส่วนกลุ่มเปราะบาง", "Population Composition"),
            color_discrete_sequence=VULN_COLORS,
            hole=0.5,
        )
        fig_donut.update_traces(
            textinfo="percent+label",
            hovertemplate="%{label}: %{value:,} " + _t("คน","ppl") + " (%{percent})<extra></extra>",
        )
        fig_donut.update_layout(
            height=340, margin=dict(t=50,b=10,l=5,r=5),
            showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
        )
        col1.plotly_chart(fig_donut, use_container_width=True)

    # Horizontal bar: % of total
    with col2:
        cats   = [_t("ผู้สูงอายุ","Elderly"), _t("ผู้พิการ","Disabled"),
                  _t("ติดเตียง","Bedridden"), _t("อยู่คนเดียว","Living Alone")]
        counts = [elderly_n, disabled_n, bedridden_n, alone_n]
        pcts   = [round(c/total*100,1) for c in counts]
        fig_h = go.Figure(go.Bar(
            x=pcts, y=cats, orientation="h",
            marker_color=VULN_COLORS[:4],
            text=[f"{p}%  ({c:,} {_t('คน','ppl')})" for p,c in zip(pcts,counts)],
            textposition="outside",
        ))
        fig_h.update_layout(
            title=_t("% ต่อประชากรทั้งหมด", "% of Total Population"),
            xaxis=dict(range=[0, max(pcts)*1.3 if pcts else 10],
                       title=_t("เปอร์เซ็นต์","Percentage (%)")),
            yaxis=dict(title=""),
            height=340, margin=dict(t=50,b=30,l=10,r=80),
            paper_bgcolor="rgba(0,0,0,0)", showlegend=False,
        )
        col2.plotly_chart(fig_h, use_container_width=True)

    # CVI risk gauge funnel
    with col3:
        CVI_ORDER  = ["critical","high","moderate","low"]
        CVI_TH     = {"critical":"🔴 วิกฤต","high":"🟠 สูง","moderate":"🟡 ปานกลาง","low":"🟢 ต่ำ"}
        CVI_EN     = {"critical":"🔴 Critical","high":"🟠 High","moderate":"🟡 Moderate","low":"🟢 Low"}
        CVI_COLORS = {"critical":"#EF4444","high":"#F97316","moderate":"#EAB308","low":"#22C55E"}
        cvi_map = {r[0]: r[1] for r in cvi_dist}
        is_th = st.session_state.get("lang","TH") == "TH"
        lmap  = CVI_TH if is_th else CVI_EN
        if cvi_map:
            cvi_labels = [lmap.get(k,k) for k in CVI_ORDER if k in cvi_map]
            cvi_vals   = [cvi_map[k] for k in CVI_ORDER if k in cvi_map]
            cvi_colors = [CVI_COLORS.get(k,"#9CA3AF") for k in CVI_ORDER if k in cvi_map]
            fig_cvi = go.Figure(go.Funnel(
                y=cvi_labels, x=cvi_vals,
                marker=dict(color=cvi_colors),
                textinfo="value+percent total",
                hovertemplate="%{y}: %{x:,} " + _t("ราย","cases") + "<extra></extra>",
            ))
            fig_cvi.update_layout(
                title=_t("ระดับความเปราะบาง (CVI)", "Vulnerability Level (CVI)"),
                height=340, margin=dict(t=50,b=10,l=5,r=5),
                paper_bgcolor="rgba(0,0,0,0)",
            )
            col3.plotly_chart(fig_cvi, use_container_width=True)
        else:
            col3.info(_t("ยังไม่มีข้อมูล CVI", "No CVI data yet."))

    st.divider()

    # ── Section 2: Chronic disease analysis ──────────────────────────────────
    st.subheader("💊 " + _t("วิเคราะห์โรคเรื้อรัง", "Chronic Disease Analysis"))

    dm  = int(hp_row.diabetes     or 0)
    ht  = int(hp_row.hypertension or 0)
    hd  = int(hp_row.heart        or 0)
    hm  = int(hp_row.homebound    or 0)

    col4, col5 = st.columns(2)

    with col4:
        # Stacked gauge-style bar showing disease count vs population
        from sqlalchemy import select as _sel
        with get_sync_db() as _db:
            total_profiles = _db.execute(
                _sel(func.count()).select_from(HealthProfile).where(HealthProfile.is_deleted == False)
            ).scalar() or 1

        diseases = {
            _t("เบาหวาน","Diabetes"):        dm,
            _t("ความดันโลหิตสูง","Hypertension"): ht,
            _t("โรคหัวใจ","Heart Disease"):  hd,
            _t("ติดบ้าน","Homebound"):       hm,
        }
        d_colors = ["#EF4444","#F97316","#8B5CF6","#3B82F6"]
        d_pcts = [round(v/total_profiles*100,1) for v in diseases.values()]

        fig_d = go.Figure()
        for i,(label,val) in enumerate(diseases.items()):
            pct = d_pcts[i]
            fig_d.add_trace(go.Bar(
                name=label,
                x=[pct], y=[label],
                orientation="h",
                marker_color=d_colors[i],
                text=f"{pct}% ({val:,})",
                textposition="auto",
                hovertemplate=f"{label}: {val:,} " + _t("ราย","cases") +
                              f" ({pct}% " + _t("ของโปรไฟล์ทั้งหมด","of profiles") + ")<extra></extra>",
            ))
        fig_d.update_layout(
            title=_t("อัตราความชุกโรคเรื้อรัง (% ของโปรไฟล์ที่มี)",
                     "Chronic Disease Prevalence (% of Profiles)"),
            xaxis=dict(title=_t("เปอร์เซ็นต์","Percentage (%)"), range=[0,max(d_pcts)*1.3 if d_pcts else 10]),
            yaxis=dict(title=""),
            height=320, margin=dict(t=50,b=30,l=10,r=80),
            showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
        )
        col4.plotly_chart(fig_d, use_container_width=True)

    with col5:
        # Radar chart: disease vs elderly population
        elderly_total = elderly_n or 1
        categories = [
            _t("เบาหวาน","Diabetes"),
            _t("ความดันโลหิตสูง","Hypertension"),
            _t("โรคหัวใจ","Heart Disease"),
            _t("ติดบ้าน","Homebound"),
        ]
        vals = [
            round(dm/total_profiles*100,1),
            round(ht/total_profiles*100,1),
            round(hd/total_profiles*100,1),
            round(hm/total_profiles*100,1),
        ]
        fig_radar = go.Figure(go.Scatterpolar(
            r=vals + [vals[0]],
            theta=categories + [categories[0]],
            fill="toself",
            fillcolor="rgba(239,68,68,0.15)",
            line=dict(color="#EF4444", width=2),
            name=_t("ความชุกของโรค","Disease Prevalence"),
        ))
        fig_radar.update_layout(
            title=_t("เรดาร์ความชุกโรค","Disease Prevalence Radar"),
            polar=dict(radialaxis=dict(visible=True, ticksuffix="%", range=[0, max(vals)*1.3 if vals else 10])),
            height=320, margin=dict(t=50,b=20,l=20,r=20),
            showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
        )
        col5.plotly_chart(fig_radar, use_container_width=True)

    st.divider()

    # ── Section 3: Referral & Alert analysis ─────────────────────────────────
    st.subheader("📤 " + _t("วิเคราะห์การส่งต่อและการแจ้งเตือน",
                             "Referral & Alert Analysis"))

    REF_STATUS_TH = {
        "pending":"รอดำเนินการ","in_progress":"กำลังดำเนินการ",
        "completed":"เสร็จสิ้น","cancelled":"ยกเลิก",
    }
    REF_COLORS = {
        "pending":"#F97316","in_progress":"#3B82F6",
        "completed":"#22C55E","cancelled":"#9CA3AF",
    }
    ref_map = {r[0]: r[1] for r in ref_status}
    col6, col7 = st.columns(2)

    with col6:
        if ref_map:
            is_th2 = st.session_state.get("lang","TH") == "TH"
            r_labels = [REF_STATUS_TH.get(k,k) if is_th2 else k for k in ref_map]
            r_vals   = list(ref_map.values())
            r_colors = [REF_COLORS.get(k,"#6B7280") for k in ref_map]
            total_refs = sum(r_vals) or 1
            fig_ref = px.pie(
                names=r_labels, values=r_vals,
                title=_t("สัดส่วนสถานะการส่งต่อ","Referral Status Breakdown"),
                color_discrete_sequence=r_colors, hole=0.45,
            )
            fig_ref.update_traces(
                textinfo="percent+label",
                hovertemplate="%{label}: %{value:,} " + _t("ราย","cases") + " (%{percent})<extra></extra>",
            )
            fig_ref.update_layout(
                height=320, margin=dict(t=50,b=20,l=5,r=5),
                showlegend=True, paper_bgcolor="rgba(0,0,0,0)",
            )
            col6.plotly_chart(fig_ref, use_container_width=True)
        else:
            col6.info(_t("ยังไม่มีข้อมูลการส่งต่อ","No referral data yet."))

    with col7:
        # Completion rate gauge
        completed_refs = ref_map.get("completed", 0)
        total_refs     = sum(ref_map.values()) if ref_map else 1
        completion_pct = round(completed_refs / total_refs * 100, 1)
        alert_resolve  = 100 - round(open_warnings / max(total_referrals, 1) * 100, 1)

        fig_gauge = go.Figure()
        fig_gauge.add_trace(go.Indicator(
            mode="gauge+number+delta",
            value=completion_pct,
            title=dict(text=_t("อัตราการส่งต่อสำเร็จ","Referral Completion Rate"), font=dict(size=14)),
            number=dict(suffix="%", font=dict(size=28)),
            delta=dict(reference=80, suffix="%",
                       increasing=dict(color="#22C55E"),
                       decreasing=dict(color="#EF4444")),
            gauge=dict(
                axis=dict(range=[0,100], ticksuffix="%"),
                bar=dict(color="#22C55E" if completion_pct >= 80 else "#EF4444"),
                steps=[
                    dict(range=[0,60],  color="#FEE2E2"),
                    dict(range=[60,80], color="#FEF9C3"),
                    dict(range=[80,100],color="#DCFCE7"),
                ],
                threshold=dict(line=dict(color="#1e3a5f",width=3), thickness=0.8, value=80),
            ),
            domain=dict(x=[0,1], y=[0,1]),
        ))
        fig_gauge.update_layout(
            height=320, margin=dict(t=60,b=20,l=30,r=30),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        col7.plotly_chart(fig_gauge, use_container_width=True)

    st.divider()

    # ── Section 4: Operational KPI summary ───────────────────────────────────
    st.subheader("📈 " + _t("สรุปตัวชี้วัดปฏิบัติการ", "Operational KPI Summary"))

    visits_per_vol  = round(total_visits / max(total_volunteers, 1), 1)
    citizens_per_vol= round(total_citizens / max(total_volunteers, 1), 1)
    assess_rate     = round(total_assessments / max(total_citizens, 1) * 100, 1)
    ref_rate        = round(total_referrals / max(total_citizens, 1) * 100, 1)

    kpi_labels = [
        _t("การเยี่ยมบ้าน/อสม.", "Visits/Volunteer"),
        _t("ประชาชน/อสม.",       "Citizens/Volunteer"),
        _t("อัตราประเมิน %",     "Assessment Rate %"),
        _t("อัตราส่งต่อ %",      "Referral Rate %"),
    ]
    kpi_vals   = [visits_per_vol, citizens_per_vol, assess_rate, ref_rate]
    kpi_targets= [50, 140, 70, 15]
    kpi_colors = ["#22C55E" if v >= t else "#EF4444"
                  for v, t in zip(kpi_vals, kpi_targets)]

    kpi_cols = st.columns(4)
    for i, col in enumerate(kpi_cols):
        col.metric(
            kpi_labels[i],
            kpi_vals[i],
            delta=f"{round(kpi_vals[i]-kpi_targets[i],1)} " + _t("จากเป้า","vs target"),
            delta_color="normal",
        )

    # Spider / bar comparison: actual vs target
    fig_kpi = go.Figure()
    fig_kpi.add_trace(go.Bar(
        name=_t("ค่าจริง","Actual"),
        x=kpi_labels, y=kpi_vals,
        marker_color=kpi_colors,
        text=[str(v) for v in kpi_vals],
        textposition="outside",
    ))
    fig_kpi.add_trace(go.Scatter(
        name=_t("เป้าหมาย","Target"),
        x=kpi_labels, y=kpi_targets,
        mode="markers+lines",
        marker=dict(symbol="diamond", size=10, color="#1e3a5f"),
        line=dict(color="#1e3a5f", dash="dash"),
    ))
    fig_kpi.update_layout(
        title=_t("ตัวชี้วัดปฏิบัติการเทียบกับเป้าหมาย", "Operational KPIs vs Targets"),
        yaxis_title=_t("ค่า","Value"),
        height=380, margin=dict(t=50,b=30,l=30,r=30),
        legend=dict(orientation="h", y=1.1),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_kpi, use_container_width=True)


# ── Elderly Monitoring ────────────────────────────────────────────────────────

def render_elderly_monitoring() -> None:
    st.header("👴 " + t("nav_elderly_monitoring"))

    with get_sync_db() as db:
        # Elderly citizens with their profiles
        elderly = db.execute(
            select(Citizen, HealthProfile)
            .outerjoin(HealthProfile, HealthProfile.citizen_id == Citizen.id)
            .where(Citizen.is_elderly == True)
            .order_by(Citizen.full_name)
            .limit(200)
        ).all()

        total = len(elderly)
        living_alone = sum(1 for _, hp in elderly if hp and hp.lives_alone_profile)
        homebound = sum(1 for _, hp in elderly if hp and hp.is_homebound)
        no_caregiver = sum(1 for _, hp in elderly if hp and not hp.has_caregiver)
        high_cvi = db.execute(
            select(func.count()).select_from(CVIScore)
            .join(Citizen, CVIScore.citizen_id == Citizen.id)
            .where(Citizen.is_elderly == True, CVIScore.category.in_(["high", "critical"]))
        ).scalar() or 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(_t("ผู้สูงอายุทั้งหมด","Total Elderly"), total)
    c2.metric(_t("อยู่คนเดียว","Living Alone"), living_alone)
    c3.metric(_t("ติดบ้าน","Homebound"), homebound)
    c4.metric(_t("ไม่มีผู้ดูแล","No Caregiver"), no_caregiver)
    c5.metric(_t("CVI สูง/วิกฤต","High/Critical CVI"), high_cvi)

    st.divider()
    st.subheader(_t("รายชื่อผู้สูงอายุ","Elderly Citizens List"))

    import pandas as pd
    if elderly:
        df = pd.DataFrame([{
            _t("ชื่อ","Name"): c.full_name,
            _t("เบอร์โทร","Phone"): c.phone or "",
            _t("อยู่คนเดียว","Living Alone"): "✓" if hp and hp.lives_alone_profile else "",
            _t("ติดบ้าน","Homebound"): "✓" if hp and hp.is_homebound else "",
            "Has Caregiver": "✓" if hp and hp.has_caregiver else "✗",
            "Chronic Conditions": sum([
                hp.has_diabetes, hp.has_hypertension, hp.has_heart_disease
            ]) if hp else 0,
            _t("ต้องเยี่ยมบ้าน","Needs Visit"): "✓" if hp and hp.needs_home_visit else "",
        } for c, hp in elderly])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No elderly citizens registered.")


# ── Health Analytics ──────────────────────────────────────────────────────────

def render_health_analytics() -> None:
    st.header("📊 " + t("nav_health_analytics"))

    with get_sync_db() as db:
        # BMI distribution
        bmi_rows = db.execute(
            select(HealthAssessment.bmi)
            .where(HealthAssessment.bmi.isnot(None), HealthAssessment.is_deleted == False)
            .limit(5000)
        ).scalars().all()

        # BP distribution
        bp_rows = db.execute(
            select(HealthAssessment.bp_systolic)
            .where(HealthAssessment.bp_systolic.isnot(None), HealthAssessment.is_deleted == False)
            .limit(5000)
        ).scalars().all()

        # Assessment trend by month
        assessment_trend = db.execute(text("""
            SELECT TO_CHAR(assessment_date::date, 'YYYY-MM') as month, COUNT(*) as cnt
            FROM health_assessments
            WHERE is_deleted = false
            GROUP BY month ORDER BY month DESC LIMIT 12
        """)).fetchall()

        # Vulnerability monthly visits (for stacked bar)
        vuln_monthly = db.execute(text("""
            SELECT
                TO_CHAR(hv.visit_date::date, 'YYYY-MM') AS month,
                CASE
                    WHEN c.is_bedridden    = true THEN 'bedridden'
                    WHEN c.is_disabled     = true THEN 'disabled'
                    WHEN c.is_elderly      = true THEN 'elderly'
                    WHEN c.is_living_alone = true THEN 'alone'
                    WHEN c.is_pregnant     = true THEN 'pregnant'
                    ELSE 'general'
                END AS grp,
                COUNT(*) AS cnt
            FROM home_visits hv
            LEFT JOIN citizens c ON c.id = hv.citizen_id
            WHERE hv.visit_date IS NOT NULL
            GROUP BY month, grp
            ORDER BY month DESC LIMIT 120
        """)).fetchall()

        # Age pyramid
        age_rows = db.execute(text("""
            SELECT
                CASE
                    WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) < 10 THEN '0-9'
                    WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) < 20 THEN '10-19'
                    WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) < 30 THEN '20-29'
                    WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) < 40 THEN '30-39'
                    WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) < 50 THEN '40-49'
                    WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) < 60 THEN '50-59'
                    WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) < 70 THEN '60-69'
                    WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) < 80 THEN '70-79'
                    ELSE '80+'
                END as age_group,
                COUNT(*) as cnt
            FROM citizens
            WHERE date_of_birth IS NOT NULL
            GROUP BY age_group ORDER BY age_group
        """)).fetchall()

    tab1, tab2, tab3, tab4 = st.tabs([
        _t("พีระมิดอายุ","Age Pyramid"),
        _t("การกระจาย BMI","BMI Distribution"),
        _t("ความดันโลหิต","Blood Pressure"),
        _t("กลุ่มเปราะบางรายเดือน","Monthly Vulnerability Groups"),
    ])

    with tab1:
        if age_rows:
            fig = px.bar(
                x=[r[0] for r in age_rows],
                y=[r[1] for r in age_rows],
                title=_t("การกระจายประชากรตามอายุ","Population Age Distribution"),
                color_discrete_sequence=["#1e3a5f"],
                labels={"x": _t("กลุ่มอายุ","Age Group"), "y": _t("จำนวน","Count")},
                text_auto=True,
            )
            fig.update_layout(xaxis_title=_t("กลุ่มอายุ","Age Group"),
                              yaxis_title=_t("จำนวนประชาชน","Population"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(_t("ยังไม่มีข้อมูลวันเกิด","No birth date data available."))

    with tab2:
        if bmi_rows:
            avg_bmi = round(sum(bmi_rows) / len(bmi_rows), 1)
            fig = px.histogram(
                x=list(bmi_rows), nbins=30,
                title=_t("การกระจายค่า BMI","BMI Distribution"),
                color_discrete_sequence=["#2a9d8f"],
                labels={"x": "BMI", "y": _t("จำนวน","Count")},
            )
            fig.add_vline(x=18.5, line_dash="dash", line_color="blue",
                         annotation_text=_t("ผอมเกิน (18.5)","Underweight (18.5)"))
            fig.add_vline(x=23, line_dash="dash", line_color="green",
                         annotation_text=_t("ปกติ (23)","Normal (23)"))
            fig.add_vline(x=25, line_dash="dash", line_color="orange",
                         annotation_text=_t("น้ำหนักเกิน (25)","Overweight (25)"))
            fig.update_layout(xaxis_title="BMI (kg/m²)",
                              yaxis_title=_t("จำนวนคน","Count"))
            st.plotly_chart(fig, use_container_width=True)
            st.metric(_t("ค่าเฉลี่ย BMI","Average BMI"), avg_bmi)
        else:
            st.info(_t("ยังไม่มีข้อมูล BMI","No BMI data yet."))

    with tab3:
        if bp_rows:
            fig = px.histogram(
                x=list(bp_rows), nbins=30,
                title=_t("การกระจายความดันโลหิต (Systolic)","Systolic Blood Pressure Distribution"),
                color_discrete_sequence=["#e63946"],
                labels={"x": _t("ความดัน Systolic (mmHg)","Systolic BP (mmHg)"),
                        "y": _t("จำนวน","Count")},
            )
            fig.add_vline(x=140, line_dash="dash", line_color="red",
                         annotation_text=_t("ความดันสูง (140)","Elevated (140)"))
            fig.update_layout(
                xaxis_title=_t("ความดัน Systolic (mmHg)","Systolic BP (mmHg)"),
                yaxis_title=_t("จำนวนคน","Count"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(_t("ยังไม่มีข้อมูลความดันโลหิต","No blood pressure data yet."))

    with tab4:
        # ── กลุ่มเปราะบางรายเดือน: summary + stacked bar + 100% bar ─────────
        VULN_TH = {
            "bedridden": _t("ติดเตียง","Bedridden"),
            "disabled":  _t("ผู้พิการ","Disabled"),
            "elderly":   _t("ผู้สูงอายุ","Elderly"),
            "alone":     _t("อยู่คนเดียว","Lives Alone"),
            "pregnant":  _t("ตั้งครรภ์","Pregnant"),
            "general":   _t("ประชากรทั่วไป","General"),
        }
        VULN_COLORS = {
            "bedridden":"#EF4444","disabled":"#8B5CF6","elderly":"#F97316",
            "alone":"#3B82F6","pregnant":"#EC4899","general":"#D1D5DB",
        }
        GROUPS_ORDER = ["bedridden","disabled","elderly","alone","pregnant","general"]

        if vuln_monthly:
            all_months_raw = sorted(set(r[0] for r in vuln_monthly))[-12:]
            all_months_be  = format_chart_months(all_months_raw)
            pivot = {g: [] for g in GROUPS_ORDER}
            month_totals = []
            for mraw in all_months_raw:
                mdata = {r[1]: r[2] for r in vuln_monthly if r[0]==mraw}
                tot = sum(mdata.values())
                month_totals.append(tot)
                for g in GROUPS_ORDER:
                    pivot[g].append(mdata.get(g, 0))

            # Summary cards — latest month
            latest_month = all_months_be[-1] if all_months_be else "—"
            latest_data  = {r[1]: r[2] for r in vuln_monthly
                            if r[0] == all_months_raw[-1]} if all_months_raw else {}
            latest_total = sum(latest_data.values())
            st.markdown(
                f"**{_t('เดือนล่าสุด','Latest Month')}: {latest_month}**  —  "
                f"{_t('กลุ่มเปราะบางทั้งหมด','Total vulnerable visits')}: "
                f"**{latest_total:,}** {_t('ครั้ง','visits')}"
            )
            sc_cols = st.columns(len(GROUPS_ORDER))
            for i, g in enumerate(GROUPS_ORDER):
                cnt = latest_data.get(g, 0)
                pct = round(cnt / max(latest_total, 1) * 100, 1)
                sc_cols[i].metric(VULN_TH[g], f"{cnt:,}", f"{pct}%", delta_color="off")

            st.divider()

            # Stacked bar — absolute counts with total annotation
            fig_stack = go.Figure()
            for g in GROUPS_ORDER:
                if any(v > 0 for v in pivot[g]):
                    fig_stack.add_trace(go.Bar(
                        name=VULN_TH[g], x=all_months_be, y=pivot[g],
                        marker_color=VULN_COLORS[g],
                        text=[f"{v:,}" if v > 0 else "" for v in pivot[g]],
                        textposition="inside",
                        textfont=dict(size=10, color="white"),
                        hovertemplate=(
                            "<b>%{x}</b><br>" + VULN_TH[g] +
                            ": %{y:,} " + _t("ครั้ง","visits") + "<extra></extra>"
                        ),
                    ))
            fig_stack.update_layout(
                barmode="stack",
                title=_t("จำนวนการเยี่ยมบ้านแยกกลุ่มเปราะบางรายเดือน (พ.ศ.)",
                         "Monthly Visits by Vulnerability Group (BE)"),
                xaxis_title=_t("เดือน (พ.ศ.)","Month (BE)"),
                yaxis_title=_t("จำนวนครั้งการเยี่ยม","Visits"),
                legend_title=_t("กลุ่มเปราะบาง","Vulnerability Group"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                height=420, paper_bgcolor="rgba(0,0,0,0)",
                annotations=[
                    dict(x=all_months_be[i], y=month_totals[i],
                         text=f"<b>{month_totals[i]:,}</b>",
                         showarrow=False, yanchor="bottom",
                         font=dict(size=11, color="#1B3A6B"))
                    for i in range(len(all_months_be))
                ],
            )
            st.plotly_chart(fig_stack, use_container_width=True)

            # 100% stacked bar
            fig_pct = go.Figure()
            for g in GROUPS_ORDER:
                if any(v > 0 for v in pivot[g]):
                    pcts = [round(pivot[g][i]/max(month_totals[i],1)*100,1)
                            for i in range(len(all_months_be))]
                    fig_pct.add_trace(go.Bar(
                        name=VULN_TH[g], x=all_months_be, y=pcts,
                        marker_color=VULN_COLORS[g],
                        hovertemplate=(
                            "<b>%{x}</b><br>" + VULN_TH[g] + ": %{y}%<extra></extra>"
                        ),
                    ))
            fig_pct.update_layout(
                barmode="relative",
                title=_t("สัดส่วนกลุ่มเปราะบางในการเยี่ยมบ้านรายเดือน (%)",
                         "Monthly Visit Share by Vulnerability Group (%)"),
                xaxis_title=_t("เดือน (พ.ศ.)","Month (BE)"),
                yaxis=dict(title=_t("สัดส่วน (%)","Share (%)"),
                           ticksuffix="%", range=[0,100]),
                legend_title=_t("กลุ่มเปราะบาง","Vulnerability Group"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                showlegend=False, height=320,
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_pct, use_container_width=True)
        else:
            st.info(_t(
                "ยังไม่มีข้อมูลการเยี่ยมบ้าน กรุณาบันทึกการเยี่ยมบ้านก่อน",
                "No visit data yet. Please record home visits first."
            ))
