"""Executive Command Center V2 — enterprise-grade analytics experience."""
from __future__ import annotations


def _t(th: str, en: str) -> str:
    import streamlit as _st
    return th if _st.session_state.get("lang","TH") == "TH" else en


import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import streamlit as st

from app.modules.analytics_v2.data_service import (
    generate_insights, load_alert_stats, load_chronic_disease_stats,
    load_gis_data, load_population_stats, load_referral_stats,
    load_risk_stats, load_visit_stats,
)

ENTERPRISE_CSS = """
<style>
/* Enterprise KPI Cards */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 12px;
    margin-bottom: 20px;
}
.kpi-card {
    background: white;
    border-radius: 14px;
    padding: 16px 14px;
    border: 1px solid #E5E7EB;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    position: relative;
    overflow: hidden;
    transition: transform 0.15s, box-shadow 0.15s;
}
.kpi-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.1); }
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
}
.kpi-blue::before   { background: linear-gradient(90deg, #2563EB, #60A5FA); }
.kpi-red::before    { background: linear-gradient(90deg, #DC2626, #F87171); }
.kpi-amber::before  { background: linear-gradient(90deg, #D97706, #FCD34D); }
.kpi-green::before  { background: linear-gradient(90deg, #059669, #34D399); }
.kpi-purple::before { background: linear-gradient(90deg, #7C3AED, #A78BFA); }
.kpi-teal::before   { background: linear-gradient(90deg, #0D9488, #2DD4BF); }
.kpi-icon { font-size: 22px; margin-bottom: 8px; }
.kpi-value { font-size: 28px; font-weight: 800; color: #111827; line-height: 1; }
.kpi-label { font-size: 11px; color: #6B7280; margin-top: 4px; font-weight: 500; }
.kpi-delta { font-size: 11px; margin-top: 6px; font-weight: 600; }
.delta-up   { color: #059669; }
.delta-down { color: #DC2626; }
.delta-flat { color: #6B7280; }

/* Insight cards */
.insight-card {
    border-radius: 10px;
    padding: 12px 14px;
    margin-bottom: 8px;
    border-left: 4px solid;
    background: white;
}
.insight-critical { border-color: #DC2626; background: #FFF5F5; }
.insight-warning  { border-color: #D97706; background: #FFFBEB; }
.insight-opportunity { border-color: #059669; background: #F0FDF4; }
.insight-title { font-size: 13px; font-weight: 700; color: #111827; margin-bottom: 4px; }
.insight-text  { font-size: 12px; color: #6B7280; line-height: 1.5; }

/* Section headers */
.section-header {
    font-size: 14px; font-weight: 700; color: #1E3A8A;
    text-transform: uppercase; letter-spacing: 1px;
    margin: 20px 0 12px;
    padding-bottom: 8px;
    border-bottom: 2px solid #EFF6FF;
}
</style>
"""

COLOR_SCALE = px.colors.sequential.Blues
BRAND_COLORS = ["#2563EB", "#7C3AED", "#059669", "#D97706", "#DC2626", "#0D9488", "#9333EA"]


def _kpi_card(icon: str, value: int | str, label: str,
              color: str = "blue", delta: str = "", delta_dir: str = "flat") -> str:
    delta_class = f"delta-{delta_dir}"
    delta_html = f'<div class="kpi-delta {delta_class}">{delta}</div>' if delta else ""
    return f"""
<div class="kpi-card kpi-{color}">
  <div class="kpi-icon">{icon}</div>
  <div class="kpi-value">{value:,}</div>
  <div class="kpi-label">{label}</div>
  {delta_html}
</div>"""


def _make_gauge(value: float, max_val: float, title: str, color: str) -> go.Figure:
    pct = min(value / max(max_val, 1) * 100, 100)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct,
        number={"suffix": "%", "font": {"size": 28, "color": "#111827"}},
        title={"text": title, "font": {"size": 13, "color": "#6B7280"}},
        gauge={
            "axis": {"range": [0, 100], "tickfont": {"size": 10}},
            "bar": {"color": color},
            "bgcolor": "#F3F4F6",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 50], "color": "#FEF3C7"},
                {"range": [50, 80], "color": "#DBEAFE"},
                {"range": [80, 100], "color": "#DCFCE7"},
            ],
            "threshold": {"line": {"color": color, "width": 3}, "value": 80},
        },
    ))
    fig.update_layout(height=200, margin=dict(t=40, b=10, l=20, r=20),
                      paper_bgcolor="white", plot_bgcolor="white")
    return fig


def render_executive_v2() -> None:
    st.markdown(ENTERPRISE_CSS, unsafe_allow_html=True)

    # Load all data
    with st.spinner("Loading intelligence data..."):
        pop     = load_population_stats()
        chronic = load_chronic_disease_stats()
        alerts  = load_alert_stats()
        visits  = load_visit_stats()
        refs    = load_referral_stats()
        risk    = load_risk_stats()
        gis     = load_gis_data()

    # Refresh
    col_h, col_r = st.columns([8, 1])
    col_h.markdown(
        f'<div style="font-size:12px;color:#6B7280;margin-bottom:4px;">{_t("ข้อมูลเชิงลึกแบบเรียลไทม์", "LIVE INTELLIGENCE")}</div>',
        unsafe_allow_html=True
    )
    if col_r.button("⟳ " + _t("รีเฟรช","Refresh"), key="exec_refresh"):
        st.cache_data.clear()
        st.rerun()

    # ── MODULE 1: EXECUTIVE KPIs ──────────────────────────────────────────────
    st.markdown(f'<div class="section-header">📊 {_t("ตัวชี้วัดผู้บริหาร", "Executive KPIs")}</div>', unsafe_allow_html=True)

    total_chronic_pop = (chronic["diabetes"] + chronic["hypertension"] +
                         chronic["heart_disease"] + chronic["stroke"])
    open_alerts = alerts.get("open", 0)

    kpi_html = f"""<div class="kpi-grid">
        {_kpi_card("👥", pop["total"], "ประชากรทั้งหมด" if st.session_state.get("lang","TH")=="TH" else "Total Population", "blue")}
        {_kpi_card("👴", pop["elderly"], _t("ผู้สูงอายุ (60+)", "Elderly (60+)"), "purple", f"{round(pop['elderly']/max(pop['total'],1)*100,1)}%")}
        {_kpi_card("♿", pop["disabled"], _t("ผู้พิการ","Disabled"), "teal")}
        {_kpi_card("🛏️", pop["bedridden"], _t("ติดเตียง","Bedridden"), "red", _t("ลำดับความสำคัญ","Priority") if pop["bedridden"] > 0 else "")}
        {_kpi_card("🏠", pop["living_alone"], _t("อยู่คนเดียว","Living Alone"), "amber")}
        {_kpi_card("💊", total_chronic_pop, _t("โรคเรื้อรัง","Chronic Disease"), "red")}
        {_kpi_card("⚠️", open_alerts, "การแจ้งเตือนที่เปิดอยู่" if st.session_state.get("lang","TH")=="TH" else "Open Alerts", "amber" if open_alerts < 20 else "red")}
        {_kpi_card("📤", refs["total"], _t("การส่งต่อ", "Referrals"), "blue", f"{refs['completion_rate']}% " + _t("สำเร็จ", "complete"))}
        {_kpi_card("🏃", visits.get("last_30d", 0), "การเยี่ยมบ้าน (30 วัน)" if st.session_state.get("lang","TH")=="TH" else "Visits (30d)", "green")}
    </div>"""
    st.markdown(kpi_html, unsafe_allow_html=True)

    st.divider()

    # ── MODULE 13: EXECUTIVE INSIGHTS ────────────────────────────────────────
    st.markdown(f'<div class="section-header">🧠 {_t("เครื่องมือวิเคราะห์เชิงบริหาร", "Executive Insight Engine")}</div>', unsafe_allow_html=True)

    insights = generate_insights(pop, chronic, alerts, visits, refs, risk)
    ins_col1, ins_col2 = st.columns(2)
    for i, ins in enumerate(insights):
        col = ins_col1 if i % 2 == 0 else ins_col2
        css_class = f"insight-{ins['type']}"
        with col:
            st.markdown(f"""
<div class="insight-card {css_class}">
  <div class="insight-title">{ins['icon']} {ins['title']}</div>
  <div class="insight-text">{ins['text']}</div>
</div>""", unsafe_allow_html=True)

    st.divider()

    # ── MODULE 2: POPULATION INTELLIGENCE ────────────────────────────────────
    st.markdown(f'<div class="section-header">🌏 {_t("ข้อมูลเชิงลึกประชากร", "Population Intelligence")}</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    # Population pyramid
    with col1:
        age_order = ["0-5", "6-12", "13-18", "19-35", "36-59", "60-69", "70-79", "80+"]
        male_vals, female_vals = [], []
        for ag in age_order:
            d = pop["age_groups"].get(ag, {})
            male_vals.append(-d.get("male", 0))
            female_vals.append(d.get("female", 0))

        fig_pyr = go.Figure()
        fig_pyr.add_trace(go.Bar(y=age_order, x=male_vals, orientation="h",
                                  name=_t("ชาย","Male"), marker_color="#2563EB",
                                  hovertemplate="%{y}: %{x:.0f}<extra></extra>"))
        fig_pyr.add_trace(go.Bar(y=age_order, x=female_vals, orientation="h",
                                  name=_t("หญิง","Female"), marker_color="#EC4899",
                                  hovertemplate="%{y}: %{x}<extra></extra>"))
        fig_pyr.update_layout(
            title=_t("พีระมิดประชากร",_t("พีระมิดประชากร","Population Pyramid")), barmode="overlay",
            height=320, margin=dict(t=40, b=20, l=40, r=20),
            xaxis=dict(title="Population", tickformat=","),
            paper_bgcolor="white", plot_bgcolor="white",
            legend=dict(orientation="h", y=-0.15),
        )
        st.plotly_chart(fig_pyr, use_container_width=True)

    # Gender donut
    with col2:
        g_data = pop.get("gender", {})
        if g_data:
            fig_g = px.pie(
                names=list(g_data.keys()), values=list(g_data.values()),
                title=_t("การกระจายตามเพศ","Gender Distribution"), hole=0.6,
                color_discrete_sequence=["#2563EB", "#EC4899", "#059669"],
            )
            fig_g.update_layout(height=320, margin=dict(t=40, b=20, l=10, r=10),
                                  paper_bgcolor="white")
            fig_g.update_traces(textinfo="percent+label",
                                 hovertemplate="%{label}: %{value:,}<extra></extra>")
            st.plotly_chart(fig_g, use_container_width=True)
        else:
            st.info("No gender data available.")

    # Vulnerability breakdown
    with col3:
        vuln_data = {
            "Elderly": pop["elderly"],
            _t("ผู้พิการ","Disabled"): pop["disabled"],
            _t("ติดเตียง","Bedridden"): pop["bedridden"],
            _t("อยู่คนเดียว","Living Alone"): pop["living_alone"],
            "Pregnant": pop["pregnant"],
        }
        fig_v = px.bar(
            x=list(vuln_data.keys()), y=list(vuln_data.values()),
            title=_t("การกระจายความเปราะบาง","Vulnerability Distribution"),
            color=list(vuln_data.values()),
            color_continuous_scale=["#DBEAFE", "#2563EB"],
            text_auto=True,
        )
        fig_v.update_layout(height=320, margin=dict(t=40, b=20, l=10, r=10),
                              paper_bgcolor="white", showlegend=False,
                              coloraxis_showscale=False)
        st.plotly_chart(fig_v, use_container_width=True)

    st.divider()

    # ── MODULE 4: CHRONIC DISEASE ANALYTICS ──────────────────────────────────
    st.markdown(f'<div class="section-header">💊 {_t("วิเคราะห์โรคเรื้อรัง", "Chronic Disease Analytics")}</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])
    with col1:
        diseases = {
            _t("เบาหวาน", "Diabetes"): chronic["diabetes"],
            _t("ความดันโลหิตสูง", "Hypertension"): chronic["hypertension"],
            _t("ไขมันในเลือดสูง", "Dyslipidemia"): chronic["dyslipidemia"],
            _t("โรคหัวใจ", "Heart Disease"): chronic["heart_disease"],
            _t("โรคหลอดเลือดสมอง", "Stroke"): chronic["stroke"],
            _t("โรคไต", "Kidney Disease"): chronic["kidney_disease"],
            _t("มะเร็ง", "Cancer"): chronic["cancer"],
            _t("โรคปอด", "Lung Disease"): chronic["lung_disease"],
        }
        diseases = dict(sorted(diseases.items(), key=lambda x: x[1], reverse=True))
        fig_d = px.bar(
            x=list(diseases.values()), y=list(diseases.keys()),
            orientation="h", title=_t("อันดับภาระโรค", "Disease Burden Ranking"),
            color=list(diseases.values()),
            color_continuous_scale=["#DBEAFE", "#1D4ED8", "#7C3AED"],
            text_auto=True,
        )
        fig_d.update_layout(height=340, margin=dict(t=40, b=20, l=120, r=20),
                              paper_bgcolor="white", coloraxis_showscale=False)
        st.plotly_chart(fig_d, use_container_width=True)

    with col2:
        total_p = max(chronic["total_profiles"], 1)
        rates = {k: round(v / total_p * 100, 1) for k, v in diseases.items()}
        fig_r = go.Figure()
        categories = list(rates.keys())
        values = list(rates.values())
        fig_r.add_trace(go.Scatterpolar(
            r=values, theta=categories, fill="toself",
            fillcolor="rgba(37,99,235,0.15)", line_color="#2563EB",
            name=_t("อัตราความชุก %", "Prevalence %"),
        ))
        fig_r.update_layout(
            title=_t("เรดาร์ความชุกของโรค", "Disease Prevalence Radar"),
            polar=dict(radialaxis=dict(visible=True, range=[0, max(values or [1]) * 1.2])),
            height=340, margin=dict(t=50, b=20, l=30, r=30),
            paper_bgcolor="white",
        )
        st.plotly_chart(fig_r, use_container_width=True)

    st.divider()

    # ── MODULE 5 & 12: RISK INTELLIGENCE ─────────────────────────────────────
    st.markdown(f'<div class="section-header">🎯 {_t("ข้อมูลเชิงลึกความเสี่ยงชุมชน", "Community Risk Intelligence")}</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        risk_dist = {
            _t("วิกฤต", "Critical"): risk.get("critical", 0),
            _t("สูง", "High"): risk.get("high", 0),
            _t("ปานกลาง", "Moderate"): risk.get("moderate", 0),
            _t("ต่ำ", "Low"): risk.get("low", 0),
        }
        fig_risk = px.funnel(
            y=list(risk_dist.keys()), x=list(risk_dist.values()),
            title=_t("ระดับความเสี่ยง", "Risk Severity Funnel"),
            color_discrete_sequence=["#DC2626", "#D97706", "#2563EB", "#059669"],
        )
        fig_risk.update_layout(height=300, margin=dict(t=40, b=10, l=60, r=10),
                                 paper_bgcolor="white")
        st.plotly_chart(fig_risk, use_container_width=True)

    with col2:
        if risk.get("top_citizens"):
            df_top = pd.DataFrame(risk["top_citizens"])
            fig_top = px.bar(
                df_top, x="score", y="name", orientation="h",
                title=_t("10 อันดับประชาชนที่มีความสำคัญสูง", "Top 10 High Priority Citizens"),
                color="score",
                color_continuous_scale=["#FEF3C7", "#DC2626"],
                text_auto=True,
            )
            fig_top.update_layout(height=300, margin=dict(t=40, b=10, l=100, r=10),
                                   paper_bgcolor="white", coloraxis_showscale=False)
            st.plotly_chart(fig_top, use_container_width=True)
        else:
            st.info("เรียกใช้ Risk Engine เพื่อดูอันดับความสำคัญ" if st.session_state.get("lang","TH")=="TH" else "Run Risk Engine to see priority rankings.")

    with col3:
        # Gauge: risk coverage
        total_scored = sum(risk_dist.values())
        fig_g = _make_gauge(total_scored, pop["total"], _t("ประชากรที่ประเมินแล้ว", "Population Scored"), "#2563EB")
        st.plotly_chart(fig_g, use_container_width=True)

        total_risk = risk.get("critical", 0) + risk.get("high", 0)
        st.metric("⚠️ " + _t("ความสำคัญสูง+วิกฤต", "High+Critical Priority"), total_risk,
                  help=_t("ประชาชนที่ต้องการการสนับสนุนจากชุมชนทันที", "Citizens needing immediate community support"))

    st.divider()

    # ── MODULE 6: ALERT MANAGEMENT ───────────────────────────────────────────
    st.markdown(f'<div class="section-header">⚠️ {_t("ศูนย์จัดการการแจ้งเตือน", "Alert Management Center")}</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        sev_data = {
            _t("วิกฤต", "Critical"): alerts.get("critical", 0),
            _t("สูง", "High"): alerts.get("high", 0),
            _t("ปานกลาง", "Medium"): alerts.get("medium", 0),
            _t("ต่ำ", "Low"): alerts.get("low", 0),
        }
        fig_sev = px.pie(
            names=list(sev_data.keys()), values=list(sev_data.values()),
            title=_t("ระดับความรุนแรงของการแจ้งเตือน", "Open Alert Severity"),
            color_discrete_map={
                _t("วิกฤต", "Critical"): "#DC2626", _t("สูง", "High"): "#D97706",
                _t("ปานกลาง", "Medium"): "#2563EB", _t("ต่ำ", "Low"): "#059669",
            },
            hole=0.5,
        )
        fig_sev.update_layout(height=280, margin=dict(t=40, b=10, l=10, r=10),
                               paper_bgcolor="white")
        st.plotly_chart(fig_sev, use_container_width=True)

    with col2:
        status_data = {
            _t("เปิด", "Open"): alerts.get("open", 0),
            _t("รับทราบ", "Acknowledged"): alerts.get("acknowledged", 0),
            _t("แก้ไขแล้ว", "Resolved"): alerts.get("resolved", 0),
        }
        fig_st = px.bar(
            x=list(status_data.keys()), y=list(status_data.values()),
            title=_t("การกระจายสถานะการแจ้งเตือน", "Alert Status Distribution"),
            color=list(status_data.keys()),
            color_discrete_map={
                _t("เปิด", "Open"): "#DC2626",
                _t("รับทราบ", "Acknowledged"): "#D97706",
                _t("แก้ไขแล้ว", "Resolved"): "#059669",
            },
            text_auto=True,
        )
        fig_st.update_layout(height=280, margin=dict(t=40, b=20, l=10, r=10),
                              paper_bgcolor="white", showlegend=False)
        st.plotly_chart(fig_st, use_container_width=True)

    with col3:
        if alerts.get("trend"):
            df_trend = pd.DataFrame(alerts["trend"])
            fig_at = px.area(
                df_trend, x="month", y="count",
                title=_t("แนวโน้มปริมาณการแจ้งเตือน", "Alert Volume Trend"),
                color_discrete_sequence=["#2563EB"],
            )
            fig_at.update_layout(height=280, margin=dict(t=40, b=20, l=10, r=10),
                                  paper_bgcolor="white")
            st.plotly_chart(fig_at, use_container_width=True)
        else:
            st.info(_t("ยังไม่มีข้อมูลแนวโน้มการแจ้งเตือน", "No alert trend data."))

    st.divider()

    # ── MODULE 7: HOME VISIT ANALYTICS ───────────────────────────────────────
    st.markdown(f'<div class="section-header">🏠 {_t("การดำเนินงานเยี่ยมบ้าน", "Home Visit Operations")}</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if visits.get("monthly_trend"):
            df_v = pd.DataFrame(visits["monthly_trend"])
            fig_vt = px.bar(
                df_v, x="month", y="count",
                title=_t("แนวโน้มการเยี่ยมบ้านรายเดือน", "Monthly Visit Trend"),
                color="count",
                color_continuous_scale=["#DBEAFE", "#1D4ED8"],
                text_auto=True,
            )
            fig_vt.update_layout(height=300, margin=dict(t=40, b=20, l=10, r=10),
                                  paper_bgcolor="white", coloraxis_showscale=False)
            st.plotly_chart(fig_vt, use_container_width=True)

    with col2:
        if visits.get("vol_productivity"):
            df_p = pd.DataFrame(visits["vol_productivity"])
            fig_vp = px.bar(
                df_p, x="visits", y="name", orientation="h",
                title=_t("10 อันดับประสิทธิภาพอาสาสมัคร", "Top 10 Volunteer Productivity"),
                color="visits",
                color_continuous_scale=["#EDE9FE", "#7C3AED"],
                text_auto=True,
            )
            fig_vp.update_layout(height=300, margin=dict(t=40, b=20, l=120, r=10),
                                  paper_bgcolor="white", coloraxis_showscale=False)
            st.plotly_chart(fig_vp, use_container_width=True)

    st.divider()

    # ── MODULE 8: REFERRAL ANALYTICS ─────────────────────────────────────────
    st.markdown(f'<div class="section-header">📤 {_t("วิเคราะห์การจัดการส่งต่อ", "Referral Management Analytics")}</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        fig_ref_g = _make_gauge(
            refs["completion_rate"], 100, _t("อัตราการส่งต่อสำเร็จ", "Referral Completion Rate"), "#059669"
        )
        st.plotly_chart(fig_ref_g, use_container_width=True)

    with col2:
        if refs.get("by_status"):
            fig_rs = px.pie(
                names=list(refs["by_status"].keys()),
                values=list(refs["by_status"].values()),
                title=_t("สถานะการส่งต่อ", "Referral Status"), hole=0.5,
                color_discrete_sequence=BRAND_COLORS,
            )
            fig_rs.update_layout(height=250, margin=dict(t=40, b=10, l=10, r=10),
                                  paper_bgcolor="white")
            st.plotly_chart(fig_rs, use_container_width=True)

    with col3:
        if refs.get("by_target"):
            fig_rt = px.bar(
                x=list(refs["by_target"].values()),
                y=list(refs["by_target"].keys()),
                orientation="h", title=_t("จุดหมายการส่งต่อ", "Referral Destinations"),
                color_discrete_sequence=["#2563EB"],
                text_auto=True,
            )
            fig_rt.update_layout(height=250, margin=dict(t=40, b=10, l=80, r=10),
                                  paper_bgcolor="white")
            st.plotly_chart(fig_rt, use_container_width=True)

    st.divider()

    # ── MODULE 9: GIS INTELLIGENCE ────────────────────────────────────────────
    st.markdown(f'<div class="section-header">🗺️ {_t("ข้อมูลเชิงพื้นที่สุขภาพ (GIS)", "GIS Health Intelligence")}</div>', unsafe_allow_html=True)

    if gis:
        import folium
        from streamlit_folium import st_folium

        map_type = st.selectbox(
            _t("ชั้นข้อมูล",_t("ชั้นข้อมูล","Map Layer")),
            [("ความหนาแน่นประชากร" if st.session_state.get("lang","TH")=="TH" else "Population Density"), ("ความหนาแน่นผู้สูงอายุ" if st.session_state.get("lang","TH")=="TH" else "Elderly Density"), ("ความหนาแน่นผู้พิการ" if st.session_state.get("lang","TH")=="TH" else "Disabled Density"), ("ความหนาแน่นติดเตียง" if st.session_state.get("lang","TH")=="TH" else "Bedridden Density")],
            key="gis_layer",
        )
        layer_col = {"Population Density": "pop", "Elderly Density": "elderly",
                     "Disabled Density": "disabled", "Bedridden Density": "bedridden"}
        col_key = layer_col[map_type]

        center_lat = sum(r["lat"] for r in gis) / len(gis)
        center_lon = sum(r["lon"] for r in gis) / len(gis)
        m = folium.Map(location=[center_lat, center_lon], zoom_start=12,
                       tiles="CartoDB positron")

        # Heatmap layer
        from folium.plugins import HeatMap
        heat_data = [[r["lat"], r["lon"], r[col_key]] for r in gis if r[col_key] > 0]
        if heat_data:
            HeatMap(heat_data, radius=18, blur=20, min_opacity=0.4,
                    gradient={"0.2": "#DBEAFE", "0.5": "#2563EB", "0.8": "#1E3A8A"}
                    ).add_to(m)

        # Markers
        for r in gis[:100]:
            val = r[col_key]
            if val > 0:
                color = "#DC2626" if val > 5 else "#D97706" if val > 2 else "#2563EB"
                folium.CircleMarker(
                    location=[r["lat"], r["lon"]],
                    radius=max(4, min(val * 2, 16)),
                    color=color, fill=True, fill_opacity=0.6,
                    popup=f"{r['community']}: {val} {col_key}",
                ).add_to(m)

        st_folium(m, height=420, use_container_width=True, key="map_executive_v2")
    else:
        st.info("ไม่มีข้อมูล GPS กรุณาเพิ่มครัวเรือนที่มีพิกัดละติจูด/ลองจิจูด" if st.session_state.get("lang","TH")=="TH" else "No GPS data. Add households with latitude/longitude coordinates to see GIS maps.")

    st.divider()

    # ── MODULE 11: SOCIAL DETERMINANTS ───────────────────────────────────────
    st.markdown(f'<div class="section-header">🏘️ {_t("ปัจจัยสังคมกำหนดสุขภาพ", "Social Determinants of Health")}</div>', unsafe_allow_html=True)

    try:
        from app.modules.health_profiles.model import HealthProfile
        from app.core.db_sync import get_sync_db
        with get_sync_db() as db:
            from sqlalchemy import select as sa_select
            hp = db.execute(sa_select(
                func.sum(HealthProfile.lives_alone_profile.cast(sa.Integer)).label("alone"),
                func.sum(HealthProfile.has_income_problems.cast(sa.Integer)).label("income"),
                func.sum(HealthProfile.has_food_insecurity.cast(sa.Integer)).label("food"),
                func.sum(HealthProfile.has_social_isolation.cast(sa.Integer)).label("social"),
                func.sum(HealthProfile.has_caregiver.cast(sa.Integer)).label("caregiver"),
                func.sum(HealthProfile.unsafe_bathroom.cast(sa.Integer)).label("unsafe"),
            )).one()

        sdh = {
            _t("อยู่คนเดียว", "Living Alone"): int(hp.alone or 0),
            _t("รายได้ต่ำ", "Low Income"): int(hp.income or 0),
            _t("ขาดความมั่นคงทางอาหาร", "Food Insecurity"): int(hp.food or 0),
            _t("โดดเดี่ยวทางสังคม", "Social Isolation"): int(hp.social or 0),
            _t("ไม่มีผู้ดูแล", "No Caregiver"): max(0, chronic["total_profiles"] - int(hp.caregiver or 0)),
            _t("ที่อยู่อาศัยไม่ปลอดภัย", "Unsafe Housing"): int(hp.unsafe or 0),
        }

        col1, col2 = st.columns(2)
        with col1:
            fig_sdh = go.Figure(go.Scatterpolar(
                r=list(sdh.values()), theta=list(sdh.keys()),
                fill="toself",
                fillcolor="rgba(124,58,237,0.15)",
                line_color="#7C3AED",
                name=_t("ความเสี่ยงทางสังคม", "SDH Risk"),
            ))
            fig_sdh.update_layout(
                title=_t("เรดาร์ความเปราะบางทางสังคม", "Social Vulnerability Radar"),
                polar=dict(radialaxis=dict(visible=True)),
                height=340, margin=dict(t=50, b=20, l=30, r=30),
                paper_bgcolor="white",
            )
            st.plotly_chart(fig_sdh, use_container_width=True)

        with col2:
            fig_sdh2 = px.bar(
                x=list(sdh.values()), y=list(sdh.keys()),
                orientation="h", title=_t("ตัวชี้วัดความเสี่ยงทางสังคม", "Social Risk Indicators"),
                color=list(sdh.values()),
                color_continuous_scale=["#EDE9FE", "#7C3AED"],
                text_auto=True,
            )
            fig_sdh2.update_layout(height=340, margin=dict(t=40, b=10, l=120, r=10),
                                    paper_bgcolor="white", coloraxis_showscale=False)
            st.plotly_chart(fig_sdh2, use_container_width=True)
    except Exception:
        st.info("ไม่มีข้อมูลโปรไฟล์สุขภาพสำหรับการวิเคราะห์ปัจจัยทางสังคม" if st.session_state.get("lang","TH")=="TH" else "No health profile data for social determinants analysis.")
