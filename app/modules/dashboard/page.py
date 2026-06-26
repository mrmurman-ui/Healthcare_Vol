"""Enhanced Dashboard V2.54.2C — Enterprise Intelligence Command Center."""
from __future__ import annotations

import io
from calendar import month_name
from datetime import date


def _t(th: str, en: str) -> str:
    import streamlit as _st
    return th if _st.session_state.get("lang","TH") == "TH" else en

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from app.shared.date_utils import be_month_label, format_chart_months
import streamlit as st

from app.modules.dashboard.DASHBOARD_CSS import DASHBOARD_CSS
from app.modules.dashboard.services.data_service import (
    forecast_simple, generate_ai_summary, load_all_dashboard_data,
)

BRAND = ["#2563EB","#7C3AED","#059669","#D97706","#DC2626",
         "#0D9488","#9333EA","#EC4899","#F59E0B","#6366F1"]


def _kpi(icon, val, label, color="", delta="", dcls="da"):
    cls = f"kpi kpi-{color}" if color else "kpi"
    d = f'<div class="kpi-delta {dcls}">{delta}</div>' if delta else ""
    v = f"{val:,}" if isinstance(val, int) else str(val)
    return (f'<div class="{cls}"><div class="kpi-icon">{icon}</div>'
            f'<div class="kpi-val">{v}</div><div class="kpi-lbl">{label}</div>{d}</div>')


def _section(title):
    st.markdown(f'<div class="db-section-title">{title}</div>', unsafe_allow_html=True)


def _cfg():
    return dict(paper_bgcolor="white", plot_bgcolor="white",
                font=dict(family="Segoe UI,sans-serif", size=12, color="#374151"),
                margin=dict(t=40, b=20, l=40, r=20))


def render_executive_tab(d):
    pop=d["population"]; alerts=d["alerts"]; visits=d["visits"]
    refs=d["referrals"]; vols=d["volunteers"]; tasks=d["tasks"]
    assess=d.get("assessments",{})

    _section("🧠 " + _t("สรุปผู้บริหาร AI","AI Executive Summary"))
    _PERIOD_EN = ["monthly", "weekly", "daily"]
    _PERIOD_TH = ["รายเดือน", "รายสัปดาห์", "รายวัน"]
    _is_th_d = st.session_state.get("lang", "TH") == "TH"
    _period_display = _PERIOD_TH if _is_th_d else _PERIOD_EN
    _period_idx = st.selectbox(
        _t("ช่วงเวลา", "Period"),
        range(len(_period_display)),
        format_func=lambda i: _period_display[i],
        key="ai_period",
        label_visibility="collapsed",
    )
    period = _PERIOD_EN[_period_idx]
    summary = generate_ai_summary(d, period)

    ah = "".join([
        f'<span class="alert-badge ab-crit">🚨 {alerts.get("critical",0)} Critical</span>' if alerts.get("critical",0) > 0 else "",
        f'<span class="alert-badge ab-high">⚠️ {alerts.get("high",0)} High</span>' if alerts.get("high",0) > 0 else "",
        f'<span class="alert-badge ab-med">🔵 {alerts.get("medium",0)} Medium</span>' if alerts.get("medium",0) > 0 else "",
    ])
    st.markdown(f"""
<div class="ai-summary">
  <div class="ai-header">
    <span style="font-size:22px;">🤖</span>
    <span style="font-size:16px;font-weight:700;color:#1E3A8A;">Executive Intelligence Summary</span>
    <span class="ai-badge">AI GENERATED</span>
  </div>
  <div class="alert-strip">{ah}</div>
</div>""", unsafe_allow_html=True)
    st.markdown(summary)
    st.divider()

    _section("📊 " + _t("ตัวชี้วัดหลัก","Executive KPIs"))
    total=pop.get("total",0); elderly=pop.get("elderly",0)
    active_vols=vols.get("active",0); coverage=vols.get("coverage_ratio",0)
    ref_rate=refs.get("completion_rate",0); open_alerts=alerts.get("total_open",0)
    overdue=tasks.get("overdue",0)

    kpi_html = '<div class="kpi-row">'
    kpi_html += _kpi("👥", total, _t("ประชากรทั้งหมด","Total Population"))
    kpi_html += _kpi("👴", elderly, (_t("ผู้สูงอายุ","Elderly") + f" ({round(elderly/max(total,1)*100,1)}%)"), "purple")
    kpi_html += _kpi("♿", pop.get("disabled",0), _t("ผู้พิการ","Disabled"), "teal")
    kpi_html += _kpi("🛏️", pop.get("bedridden",0), _t("ติดเตียง","Bedridden"), "red")
    kpi_html += _kpi("🏠", pop.get("living_alone",0), _t("อยู่คนเดียว","Living Alone"), "amber")
    kpi_html += _kpi("👥", active_vols, _t("อสม. ใช้งาน",_t("อสม. ใช้งาน","Active อสม.")), "green", f"{coverage:.0f}:1 ratio")
    kpi_html += _kpi("🏠", visits.get("last_30d",0), _t("เยี่ยมบ้าน (30 วัน)",_t("เยี่ยมบ้าน (30 วัน)","Visits (30d)")))
    kpi_html += _kpi("📤", refs.get("total",0), _t("การส่งต่อ","Referrals"), "green" if ref_rate>=80 else "amber", f"{ref_rate}%", "dg" if ref_rate>=80 else "dr")
    kpi_html += _kpi("⚠️", open_alerts, _t("แจ้งเตือนที่เปิด",_t("แจ้งเตือนที่เปิด","Open Alerts")), "red" if open_alerts>10 else "amber")
    kpi_html += _kpi("🚨", overdue, _t("งานเกินกำหนด","Overdue Tasks"), "red" if overdue>5 else "amber")
    kpi_html += _kpi("📋", assess.get("total",0), _t("การประเมิน",_t("การประเมิน","Assessments")))
    kpi_html += _kpi("📊", f"{ref_rate}%", _t("ส่งต่อสำเร็จ",_t("ส่งต่อสำเร็จ","Ref. Completion")), "green" if ref_rate>=80 else "red")
    kpi_html += "</div>"
    st.markdown(kpi_html, unsafe_allow_html=True)
    st.divider()

    col1,col2,col3 = st.columns(3)
    with col1:
        if visits.get("monthly") and refs.get("monthly"):
            vm_be=format_chart_months([x["month"] for x in visits["monthly"]])
            vc=[x["count"] for x in visits["monthly"]]
            rm_be=format_chart_months([x["month"] for x in refs["monthly"]])
            rc=[x["count"] for x in refs["monthly"]]
            fig=go.Figure()
            fig.add_trace(go.Scatter(x=vm_be,y=vc,name=_t("การเยี่ยมบ้าน","Visits"),mode="lines+markers",
                line=dict(color="#2563EB",width=2.5),fill="tozeroy",fillcolor="rgba(37,99,235,0.08)"))
            fig.add_trace(go.Scatter(x=rm_be,y=rc,name=_t("การส่งต่อ","Referrals"),mode="lines+markers",
                line=dict(color="#7C3AED",width=2)))
            fig.update_layout(title=_t("แนวโน้ม 12 เดือน","12-Month Trend"),height=280,
                xaxis_title=_t("เดือน (พ.ศ.)","Month (BE)"),
                yaxis_title=_t("จำนวน","Count"),
                legend=dict(orientation="h",y=-0.25),**_cfg())
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        sev={_t("วิกฤต","Critical"):alerts.get("critical",0),_t("สูง","High"):alerts.get("high",0),
             _t("ปานกลาง","Medium"):alerts.get("medium",0),_t("ต่ำ","Low"):alerts.get("low",0)}
        fig2=px.pie(names=list(sev.keys()),values=list(sev.values()),title=_t("ระดับการแจ้งเตือน","Alert Severity"),hole=0.65,
            color_discrete_map={_t("วิกฤต","Critical"):"#DC2626",_t("สูง","High"):"#D97706",_t("ปานกลาง","Medium"):"#2563EB",_t("ต่ำ","Low"):"#059669"})
        fig2.update_layout(height=280,**_cfg())
        st.plotly_chart(fig2, use_container_width=True)
    with col3:
        td={k:v for k,v in tasks.items() if k!="total" and isinstance(v,int)}
        if td:
            _STAT_TH={"new":_t("ใหม่","New"),"assigned":_t("มอบหมาย","Assigned"),
                      "in_progress":_t("กำลังดำเนิน","In Progress"),
                      "completed":_t("เสร็จสิ้น","Completed"),
                      "overdue":_t("เกินกำหนด","Overdue"),
                      "cancelled":_t("ยกเลิก","Cancelled")}
            _is_th_d = st.session_state.get("lang","TH")=="TH"
            td_labels=[_STAT_TH.get(k,k) if _is_th_d else k for k in td.keys()]
            td_colors={"new":"#6B7280","assigned":"#3B82F6","in_progress":"#F97316",
                       "completed":"#22C55E","overdue":"#EF4444","cancelled":"#9CA3AF"}
            td_bar_colors=[td_colors.get(k,"#6B7280") for k in td.keys()]
            fig3=px.bar(x=td_labels,y=list(td.values()),title=_t("สถานะงาน","Task Status"),
                text_auto=True,color=td_labels,color_discrete_sequence=td_bar_colors)
            fig3.update_layout(height=280,showlegend=False,**_cfg())
            st.plotly_chart(fig3, use_container_width=True)

    st.divider()
    _section("📈 " + _t("พยากรณ์และอันดับชุมชน","Forecast & Community Rankings"))
    col1,col2 = st.columns(2)
    with col1:
        if visits.get("monthly") and len(visits["monthly"])>=3:
            hist=[x["count"] for x in visits["monthly"]]
            fcast=forecast_simple(hist,6)
            mh=[x["month"] for x in visits["monthly"]]
            mf=[f"F+{i+1}" for i in range(6)]
            _mh_be = format_chart_months(mh)
            _mf_be = [_t(f"พยากรณ์+{i+1}",f"F+{i+1}") for i in range(6)]
            fig_f=go.Figure()
            fig_f.add_trace(go.Scatter(x=_mh_be,y=hist,
                name=_t("ค่าจริง","Actual"),line=dict(color="#2563EB",width=2.5)))
            fig_f.add_trace(go.Scatter(x=[_mh_be[-1]]+_mf_be,y=[hist[-1]]+fcast,
                name=_t("พยากรณ์","Forecast"),
                line=dict(color="#D97706",width=2,dash="dash")))
            fig_f.update_layout(
                title=_t("พยากรณ์การเยี่ยมบ้าน (6 เดือน)","Visit Demand Forecast (6mo)"),
                xaxis_title=_t("เดือน (พ.ศ.)","Month"),
                yaxis_title=_t("จำนวนการเยี่ยม","Visits"),
                height=260,**_cfg())
            st.plotly_chart(fig_f, use_container_width=True)
    with col2:
        if d.get("scorecards"):
            sc_df=pd.DataFrame(d["scorecards"][:10])
            fig_sc=px.bar(sc_df,x="score",y="name",orientation="h",title=_t("อันดับชุมชน","Community Rankings"),
                color="score",color_continuous_scale=["#FEF3C7","#2563EB"],text_auto=True)
            fig_sc.update_layout(height=260,coloraxis_showscale=False,**_cfg())
            st.plotly_chart(fig_sc, use_container_width=True)


def render_operations_tab(d):
    visits=d["visits"]; refs=d["referrals"]; vols=d["volunteers"]
    assess=d.get("assessments",{})

    _section("🏠 " + _t("ปฏิบัติการเยี่ยมบ้านและประเมินสุขภาพ","Home Visit & Assessment Operations"))
    col1,col2 = st.columns(2)
    with col1:
        if visits.get("monthly"):
            _vm_months = format_chart_months([r["month"] for r in visits["monthly"]])
            _vm_counts = [r["count"] for r in visits["monthly"]]
            fig=go.Figure(go.Bar(
                x=_vm_months, y=_vm_counts,
                marker=dict(color=_vm_counts, colorscale=["#DBEAFE","#1D4ED8"],
                            showscale=False),
                text=_vm_counts, textposition="outside",
            ))
            fig.update_layout(
                title=_t("การเยี่ยมบ้านรายเดือน (พ.ศ.)","Monthly Home Visits (BE)"),
                xaxis_title=_t("เดือน (พ.ศ.)","Month (BE)"),
                yaxis_title=_t("จำนวนครั้ง","Visits"),
                height=300,**_cfg())
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        # ── กลุ่มเปราะบาง 3 ส่วน ─────────────────────────────────────────────
        from app.core.db_sync import get_sync_db
        from sqlalchemy import text as _text2
        _vuln_rows = []
        _err_msg = ""
        try:
            with get_sync_db() as _vdb:
                _vuln_rows = _vdb.execute(_text2("""
                    SELECT
                        TO_CHAR(hv.visit_date::date,'YYYY-MM') AS month,
                        CASE
                          WHEN COALESCE(c.is_bedridden,false)=true  THEN 'bedridden'
                          WHEN COALESCE(c.is_disabled,false)=true   THEN 'disabled'
                          WHEN COALESCE(c.is_elderly,false)=true    THEN 'elderly'
                          ELSE 'general'
                        END AS grp,
                        COUNT(*) AS cnt
                    FROM home_visits hv
                    LEFT JOIN citizens c ON c.id = hv.citizen_id
                    WHERE hv.visit_date IS NOT NULL
                    GROUP BY 1,2
                    ORDER BY 1 DESC
                    LIMIT 84
                """)).fetchall()
        except Exception as _ex:
            _err_msg = str(_ex)

        if _vuln_rows:
            _VTH = {"bedridden":_t("ติดเตียง","Bedridden"),
                    "disabled": _t("ผู้พิการ","Disabled"),
                    "elderly":  _t("ผู้สูงอายุ","Elderly"),
                    "general":  _t("ทั่วไป","General")}
            _VC  = {"bedridden":"#EF4444","disabled":"#8B5CF6",
                    "elderly":"#F97316","general":"#D1D5DB"}
            _GO  = ["bedridden","disabled","elderly","general"]

            _mraw = sorted(set(r[0] for r in _vuln_rows))[-7:]
            _mbe  = format_chart_months(_mraw)
            _piv  = {g: [] for g in _GO}
            _tots = []
            for _m in _mraw:
                _md = {r[1]: r[2] for r in _vuln_rows if r[0] == _m}
                _tots.append(sum(_md.values()))
                for g in _GO:
                    _piv[g].append(_md.get(g, 0))

            # ── ส่วนที่ 1: Metric cards (เดือนล่าสุด) ────────────────────────
            _ld   = {r[1]: r[2] for r in _vuln_rows if r[0] == _mraw[-1]}
            _ltot = sum(_ld.values())
            st.markdown(f"**{_mbe[-1]} — {_t('รวม','Total')} {_ltot:,} {_t('ครั้ง','visits')}**")
            _active_groups = [g for g in _GO if _ld.get(g,0) > 0]
            _mc = st.columns(max(len(_active_groups),1))
            for _ci, g in enumerate(_active_groups):
                _cnt = _ld.get(g,0)
                _mc[_ci].metric(_VTH[g], f"{_cnt:,}",
                                f"{round(_cnt/max(_ltot,1)*100,1)}%",
                                delta_color="off")

            # ── ส่วนที่ 2: Stacked bar (จำนวน) ───────────────────────────────
            _fs = go.Figure()
            for g in _GO:
                if any(v > 0 for v in _piv[g]):
                    _fs.add_trace(go.Bar(
                        name=_VTH[g], x=_mbe, y=_piv[g],
                        marker_color=_VC[g],
                        text=[str(v) if v > 0 else "" for v in _piv[g]],
                        textposition="inside",
                        textfont=dict(size=9, color="white"),
                        hovertemplate="<b>%{x}</b><br>"+_VTH[g]+": %{y:,}<extra></extra>",
                    ))
            _fs.update_layout(
                barmode="stack",
                title=_t("การเยี่ยมบ้านแยกกลุ่มเปราะบาง (พ.ศ.)",
                         "Visits by Vulnerability Group (BE)"),
                xaxis_title=_t("เดือน (พ.ศ.)","Month (BE)"),
                yaxis_title=_t("จำนวนครั้ง","Visits"),
                legend=dict(orientation="h", y=-0.3, font=dict(size=10)),
                annotations=[dict(x=_mbe[i], y=_tots[i],
                                  text=f"<b>{_tots[i]:,}</b>",
                                  showarrow=False, yanchor="bottom",
                                  font=dict(size=10, color="#1B3A6B"))
                             for i in range(len(_mbe))],
                height=320, **_cfg())
            st.plotly_chart(_fs, use_container_width=True)

            # ── ส่วนที่ 3: 100% stacked bar (สัดส่วน) ────────────────────────
            _fp = go.Figure()
            for g in _GO:
                if any(v > 0 for v in _piv[g]):
                    _fp.add_trace(go.Bar(
                        name=_VTH[g], x=_mbe,
                        y=[round(_piv[g][i]/max(_tots[i],1)*100,1)
                           for i in range(len(_mbe))],
                        marker_color=_VC[g], showlegend=False,
                        hovertemplate="<b>%{x}</b><br>"+_VTH[g]+": %{y}%<extra></extra>",
                    ))
            _fp.update_layout(
                barmode="relative",
                title=_t("สัดส่วนกลุ่มเปราะบาง (%)","Vulnerability Share (%)"),
                xaxis_title=_t("เดือน (พ.ศ.)","Month (BE)"),
                yaxis=dict(title=_t("สัดส่วน (%)","Share (%)"),
                           ticksuffix="%", range=[0,100]),
                height=260, **_cfg())
            st.plotly_chart(_fp, use_container_width=True)
        else:
            st.warning(_t(
                f"ยังไม่มีข้อมูลการเยี่ยมบ้าน{(' — '+_err_msg[:60]) if _err_msg else ''}",
                f"No visit data{(' — '+_err_msg[:60]) if _err_msg else ''}"
            ))

    _section("📤 " + _t("วิเคราะห์การส่งต่อ","Referral Analytics"))
    col1,col2,col3 = st.columns(3)
    with col1:
        rc=refs.get("completion_rate",0)
        fig_g=go.Figure(go.Indicator(mode="gauge+number",value=rc,number={"suffix":"%"},
            title={"text":_t("อัตราการส่งต่อสำเร็จ","Referral Completion")},
            gauge={"axis":{"range":[0,100]},"bar":{"color":"#059669" if rc>=80 else "#D97706"},
                   "steps":[{"range":[0,60],"color":"#FEF3C7"},{"range":[60,80],"color":"#DBEAFE"},
                             {"range":[80,100],"color":"#DCFCE7"}],
                   "threshold":{"line":{"color":"#059669","width":3},"value":80}}))
        fig_g.update_layout(height=280,**_cfg())
        st.plotly_chart(fig_g, use_container_width=True)
    with col2:
        by_s=refs.get("by_status",{})
        if by_s:
            fig_rs=px.pie(names=list(by_s.keys()),values=list(by_s.values()),
                title=_t("สถานะการส่งต่อ","Referral Status"),hole=0.55,color_discrete_sequence=BRAND)
            fig_rs.update_layout(height=280,**_cfg())
            st.plotly_chart(fig_rs, use_container_width=True)
    with col3:
        if refs.get("monthly"):
            df_rm=pd.DataFrame(refs["monthly"])
            fig_rt=px.line(df_rm,x="month",y="count",title=_t("แนวโน้มการส่งต่อ",_t("แนวโน้มการส่งต่อ","Referral Trend")),
                markers=True,color_discrete_sequence=["#7C3AED"])
            fig_rt.update_layout(height=280,**_cfg())
            st.plotly_chart(fig_rt, use_container_width=True)

    _section("👥 " + _t("ปฏิบัติการอาสาสมัคร","Volunteer Operations"))
    col1,col2 = st.columns(2)
    with col1:
        top=vols.get("top",[])
        if top:
            df_v=pd.DataFrame(top)
            fig_v=px.bar(df_v,x="visits",y="name",orientation="h",title=_t("อาสาสมัครยอดเยี่ยม 10 อันดับ","Top 10 Volunteer Productivity"),
                color="visits",color_continuous_scale=["#EDE9FE","#7C3AED"],text_auto=True)
            fig_v.update_layout(height=320,coloraxis_showscale=False,**_cfg())
            st.plotly_chart(fig_v, use_container_width=True)
    with col2:
        vs={k:v for k,v in vols.items() if k not in("active","top","coverage_ratio") and isinstance(v,int)}
        if vs:
            fig_vs=px.pie(names=list(vs.keys()),values=list(vs.values()),title=_t("สถานะอาสาสมัคร","Volunteer Status"),hole=0.5,
                color_discrete_map={"active":"#059669","inactive":"#6B7280"})
            fig_vs.update_layout(height=320,**_cfg())
            st.plotly_chart(fig_vs, use_container_width=True)


def render_population_tab(d):
    pop=d["population"]; chronic=d["chronic"]; age_groups=d.get("age_groups",[])
    ag_order=["0-14","15-24","25-44","45-59","60-69","70-79","80+"]

    _section("🌏 " + _t("พีระมิดประชากร",_t("พีระมิดประชากร","Population Pyramid")))
    col1,col2 = st.columns(2)
    with col1:
        mv,fv=[],[]
        for ag in ag_order:
            m=sum(r["count"] for r in age_groups if r["group"]==ag and r["gender"]=="male")
            f=sum(r["count"] for r in age_groups if r["group"]==ag and r["gender"]=="female")
            mv.append(-m); fv.append(f)
        fig_pyr=go.Figure()
        fig_pyr.add_trace(go.Bar(y=ag_order,x=mv,orientation="h",name=_t("ชาย","Male"),marker_color="#2563EB"))
        fig_pyr.add_trace(go.Bar(y=ag_order,x=fv,orientation="h",name=_t("หญิง","Female"),marker_color="#EC4899"))
        fig_pyr.update_layout(title=_t("พีระมิดประชากร","Population Pyramid"),barmode="overlay",height=360,
            xaxis=dict(tickformat=","),legend=dict(orientation="h",y=-0.15),**_cfg())
        st.plotly_chart(fig_pyr, use_container_width=True)
    with col2:
        total=pop.get("total",1)
        child=sum(r["count"] for r in age_groups if r["group"]=="0-14")
        working=sum(r["count"] for r in age_groups if r["group"] in("15-24","25-44","45-59"))
        fig_dist=px.pie(
            names=[_t("เด็ก (0-14)","Children (0-14)"),_t("วัยทำงาน","Working Age"),_t("ผู้สูงอายุ (60+)","Elderly (60+)"),_t("ผู้พิการ","Disabled"),_t("ติดเตียง","Bedridden"),_t("อยู่คนเดียว","Living Alone")],
            values=[child,working,pop.get("elderly",0),pop.get("disabled",0),
                    pop.get("bedridden",0),pop.get("living_alone",0)],
            title=_t("การกระจายประชากร","Population Distribution"),hole=0.55,color_discrete_sequence=BRAND)
        fig_dist.update_layout(height=360,**_cfg())
        st.plotly_chart(fig_dist, use_container_width=True)

    st.divider()
    _section("💊 " + _t("วิเคราะห์โรคเรื้อรัง","Chronic Disease Analytics"))
    _is_th_d = st.session_state.get("lang","TH")=="TH"
    _DN = {
        "Hypertension":    "ความดันโลหิตสูง",
        "Diabetes":        "เบาหวาน",
        "Dyslipidemia":    "ไขมันในเลือดสูง",
        "Heart Disease":   "โรคหัวใจ",
        "Stroke":          "โรคหลอดเลือดสมอง",
        "Cancer":          "มะเร็ง",
        "CKD":             "โรคไต",
        "COPD":            "โรคปอด",
    }
    def _dn(k): return _DN[k] if _is_th_d else k
    diseases={_dn("Hypertension"):chronic.get("hypertension",0),_dn("Diabetes"):chronic.get("diabetes",0),
              _dn("Dyslipidemia"):chronic.get("dyslipidemia",0),_dn("Heart Disease"):chronic.get("heart_disease",0),
              _dn("Stroke"):chronic.get("stroke",0),_dn("Cancer"):chronic.get("cancer",0),
              _dn("CKD"):chronic.get("kidney",0),_dn("COPD"):chronic.get("lung",0)}
    diseases=dict(sorted(diseases.items(),key=lambda x:x[1],reverse=True))
    col1,col2 = st.columns(2)
    with col1:
        fig_d=px.bar(x=list(diseases.values()),y=list(diseases.keys()),orientation="h",
            title=_t("อันดับภาระโรค","Disease Burden Ranking"),color=list(diseases.values()),
            color_continuous_scale=["#DBEAFE","#1D4ED8"],text_auto=True)
        fig_d.update_layout(height=360,coloraxis_showscale=False,**_cfg())
        st.plotly_chart(fig_d, use_container_width=True)
    with col2:
        profs=max(chronic.get("profiles",1),1)
        rates={k:round(v/profs*100,1) for k,v in diseases.items()}
        fig_r=go.Figure(go.Scatterpolar(r=list(rates.values()),theta=list(rates.keys()),
            fill="toself",fillcolor="rgba(37,99,235,0.12)",line_color="#2563EB"))
        fig_r.update_layout(title=_t("เรดาร์ความชุกของโรค","Disease Prevalence Radar"),
            polar=dict(radialaxis=dict(visible=True)),height=360,**_cfg())
        st.plotly_chart(fig_r, use_container_width=True)

    st.divider()
    _section("🏘️ " + _t("ปัจจัยสังคมและความเปราะบาง","Social Determinants & Vulnerability"))
    vuln={_t("ติดบ้าน","Homebound"):chronic.get("homebound",0),_t("โดดเดี่ยวทางสังคม","Social Isolation"):chronic.get("social_isolation",0),
          _t("ปัญหารายได้","Income Problems"):chronic.get("income_problems",0),_t("อยู่คนเดียว","Living Alone"):pop.get("living_alone",0),
          _t("ติดเตียง","Bedridden"):pop.get("bedridden",0),_t("ผู้พิการ","Disabled"):pop.get("disabled",0)}
    fig_t=px.treemap(names=list(vuln.keys()),parents=[""]*len(vuln),values=list(vuln.values()),
        title=_t("แผนภูมิความเปราะบาง","Vulnerability Treemap"),color=list(vuln.values()),
        color_continuous_scale=["#DBEAFE","#DC2626"])
    fig_t.update_layout(height=320,**_cfg())
    st.plotly_chart(fig_t, use_container_width=True)


def render_gis_tab(d):
    gis=d.get("gis",[])
    _section("🗺️ " + _t("ข้อมูลสุขภาพเชิงพื้นที่","Geographic Health Intelligence"))
    if not gis:
        st.info(_t("ไม่มีข้อมูล GPS กรุณาเพิ่มครัวเรือนที่มีพิกัดละติจูด/ลองจิจูด","No GPS data. Add households with latitude/longitude coordinates."))
        return
    layer=st.selectbox("Map Layer",
        [_t("ความหนาแน่นประชากร","Population Density"),_t("ความหนาแน่นผู้สูงอายุ","Elderly Density"),_t("ความหนาแน่นผู้พิการ","Disabled Density"),_t("ความหนาแน่นติดเตียง","Bedridden Density")],
        key="gis_db")
    lm={_t("ความหนาแน่นประชากร","Population Density"):"pop",_t("ความหนาแน่นผู้สูงอายุ","Elderly Density"):"elderly",
        _t("ความหนาแน่นผู้พิการ","Disabled Density"):"disabled",_t("ความหนาแน่นติดเตียง","Bedridden Density"):"bedridden"}
    col_key=lm[layer]
    try:
        import folium
        from folium.plugins import HeatMap
        from streamlit_folium import st_folium
        lats=[r["lat"] for r in gis]; lons=[r["lon"] for r in gis]
        m=folium.Map(location=[sum(lats)/len(lats),sum(lons)/len(lons)],
                     zoom_start=12,tiles="CartoDB positron")
        heat=[[r["lat"],r["lon"],r[col_key]] for r in gis if r[col_key]>0]
        if heat:
            try:
              HeatMap(heat,radius=20,blur=25,min_opacity=0.4,
                gradient={"0.2":"#DBEAFE","0.5":"#2563EB","0.8":"#1E3A8A"}).add_to(m)
            except Exception:
                pass
        for r in gis[:200]:
            if r[col_key]>0:
                color="#DC2626" if r[col_key]>5 else "#D97706" if r[col_key]>2 else "#2563EB"
                folium.CircleMarker(location=[r["lat"],r["lon"]],
                    radius=max(4,min(r[col_key]*2,18)),color=color,fill=True,fill_opacity=0.65,
                    popup=f"{r['community']}: {r[col_key]}").add_to(m)
        st_folium(m, height=480, use_container_width=True, key="map_page")
    except Exception as e:
        st.error(f"Map error: {e}")


def render_monthly_report(d):
    _section("📄 " + _t("รายงานสรุปประจำเดือน","Monthly Summary Report"))
    col1,col2,col3=st.columns(3)
    sel_year=col1.number_input(_t("ปี","Year"),min_value=2020,max_value=2030,
                                value=date.today().year,key="rpt_year")
    sel_month=col2.number_input(_t("เดือน","Month"),min_value=1,max_value=12,
                                 value=date.today().month,key="rpt_month")
    if col3.button("📥 " + _t("สร้างรายงาน","Generate Report"),type="primary",key="gen_rpt"):
        _build_report(d,int(sel_year),int(sel_month))


def _build_report(d, year, month):
    pop=d["population"]; chronic=d["chronic"]; alerts=d["alerts"]
    visits=d["visits"]; refs=d["referrals"]; vols=d["volunteers"]
    assess=d.get("assessments",{})
    month_str=f"{month_name[month]} {year}"

    st.success(f"✅ Report Generated: {month_str}")
    st.markdown(f"""
<div style="background:white;border-radius:14px;padding:24px 28px;
  border:1px solid #E5E7EB;box-shadow:0 4px 16px rgba(0,0,0,0.06);margin-bottom:16px;">
  <div style="font-size:20px;font-weight:800;color:#1E3A8A;">Monthly Health Summary — {month_str}</div>
  <div style="font-size:12px;color:#6B7280;margin-bottom:16px;">MKI Community Health Platform v2.54.2C</div>
  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;">
    <div style="background:#F8FAFF;border-radius:10px;padding:12px;">
      <div style="font-size:10px;color:#6B7280;text-transform:uppercase;">Population</div>
      <div style="font-size:22px;font-weight:800;color:#1E3A8A;">{pop.get("total",0):,}</div>
    </div>
    <div style="background:#F8FAFF;border-radius:10px;padding:12px;">
      <div style="font-size:10px;color:#6B7280;text-transform:uppercase;">Visits (30d)</div>
      <div style="font-size:22px;font-weight:800;color:#2563EB;">{visits.get("last_30d",0):,}</div>
    </div>
    <div style="background:#FEF2F2;border-radius:10px;padding:12px;">
      <div style="font-size:10px;color:#6B7280;text-transform:uppercase;">Open Alerts</div>
      <div style="font-size:22px;font-weight:800;color:#DC2626;">{alerts.get("total_open",0):,}</div>
    </div>
    <div style="background:#F0FDF4;border-radius:10px;padding:12px;">
      <div style="font-size:10px;color:#6B7280;text-transform:uppercase;">Ref. Completion</div>
      <div style="font-size:22px;font-weight:800;color:#059669;">{refs.get("completion_rate",0)}%</div>
    </div>
    <div style="background:#FAF5FF;border-radius:10px;padding:12px;">
      <div style="font-size:10px;color:#6B7280;text-transform:uppercase;">Active อสม.</div>
      <div style="font-size:22px;font-weight:800;color:#7C3AED;">{vols.get("active",0):,}</div>
    </div>
    <div style="background:#F0FDFA;border-radius:10px;padding:12px;">
      <div style="font-size:10px;color:#6B7280;text-transform:uppercase;">Assessments</div>
      <div style="font-size:22px;font-weight:800;color:#0D9488;">{assess.get("total",0):,}</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

    st.markdown("### 🧠 " + _t("บทสรุปผู้บริหาร","Executive Narrative"))
    summary=generate_ai_summary(d,"monthly")
    st.markdown(summary)

    col1,col2=st.columns(2)
    with col1:
        if visits.get("monthly"):
            fig=px.bar(pd.DataFrame(visits["monthly"]),x="month",y="count",
                title=_t("แนวโน้มการเยี่ยมบ้าน","Visit Trend"),color_discrete_sequence=["#2563EB"],text_auto=True)
            fig.update_layout(height=260,paper_bgcolor="white",plot_bgcolor="white",
                margin=dict(t=40,b=20,l=10,r=10))
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        if refs.get("monthly"):
            fig2=px.line(pd.DataFrame(refs["monthly"]),x="month",y="count",
                title=_t("แนวโน้มการส่งต่อ",_t("แนวโน้มการส่งต่อ","Referral Trend")),markers=True,color_discrete_sequence=["#7C3AED"])
            fig2.update_layout(height=260,paper_bgcolor="white",plot_bgcolor="white",
                margin=dict(t=40,b=20,l=10,r=10))
            st.plotly_chart(fig2, use_container_width=True)

    # Excel export
    buf=io.BytesIO()
    with pd.ExcelWriter(buf,engine="openpyxl") as writer:
        pd.DataFrame({
            "Indicator":[_t("ประชากร","Population"),"Elderly",_t("ผู้พิการ","Disabled"),_t("ติดเตียง","Bedridden"),_t("อยู่คนเดียว","Living Alone"),
                         "Active Vols","Visits(30d)",_t("การส่งต่อ","Referrals"),"Ref%",_t("แจ้งเตือนที่เปิด",_t("แจ้งเตือนที่เปิด","Open Alerts")),
                         _t("วิกฤต","Critical"),_t("การประเมิน",_t("การประเมิน","Assessments"))],
            "Value":[pop.get("total",0),pop.get("elderly",0),pop.get("disabled",0),
                     pop.get("bedridden",0),pop.get("living_alone",0),vols.get("active",0),
                     visits.get("last_30d",0),refs.get("total",0),refs.get("completion_rate",0),
                     alerts.get("total_open",0),alerts.get("critical",0),assess.get("total",0)]
        }).to_excel(writer,sheet_name="Summary",index=False)
        if visits.get("monthly"):
            pd.DataFrame(visits["monthly"]).to_excel(writer,sheet_name="Visits",index=False)
        if refs.get("monthly"):
            pd.DataFrame(refs["monthly"]).to_excel(writer,sheet_name=_t("การส่งต่อ","Referrals"),index=False)
        _is_th_xl = st.session_state.get("lang","TH")=="TH"
        _cond_col = _t("โรค","Condition")
        _cond_names = [
            _t("ความดันโลหิตสูง","Hypertension"),_t("เบาหวาน","Diabetes"),
            _t("ไขมันในเลือดสูง","Dyslipidemia"),_t("โรคหัวใจ","Heart Disease"),
            _t("โรคหลอดเลือดสมอง","Stroke"),_t("มะเร็ง","Cancer"),
            _t("โรคไต","CKD"),_t("โรคปอด","COPD"),
        ]
        pd.DataFrame({
            _cond_col: _cond_names,
            _t("จำนวน","Count"):[chronic.get("hypertension",0),chronic.get("diabetes",0),chronic.get("dyslipidemia",0),
                     chronic.get("heart_disease",0),chronic.get("stroke",0),chronic.get("cancer",0),
                     chronic.get("kidney",0),chronic.get("lung",0)]
        }).to_excel(writer,sheet_name=_t("โรคเรื้อรัง","Chronic Disease"),index=False)
        if vols.get("top"):
            pd.DataFrame(vols["top"]).to_excel(writer,sheet_name="Volunteer Top10",index=False)
        if d.get("scorecards"):
            pd.DataFrame(d["scorecards"]).to_excel(writer,sheet_name="Scorecards",index=False)

    st.download_button(f"⬇️ Excel Report — {month_str}", buf.getvalue(),
        f"MKI_Health_{year}_{month:02d}.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.download_button("⬇️ " + _t("บทสรุป (ข้อความ)","Narrative (Text)"), summary.encode("utf-8"),
        f"MKI_Summary_{year}_{month:02d}.txt", "text/plain")


def render_dashboard():
    st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)

    col_h,col_r=st.columns([8,1])
    col_h.markdown(
        '<div style="font-size:11px;color:#6B7280;letter-spacing:1px;margin-bottom:4px;">'
        'COMMUNITY HEALTH INTELLIGENCE COMMAND CENTER</div>', unsafe_allow_html=True)
    if col_r.button("⟳",key="db_refresh",help=_t('รีเฟรช','Refresh')):
        st.cache_data.clear()
        st.rerun()

    with st.spinner("Loading intelligence platform..."):
        d=load_all_dashboard_data()

    tab1,tab2,tab3,tab4,tab5=st.tabs([
        "🎯 " + _t("ผู้บริหาร","Executive"),
        "⚙️ " + _t("ปฏิบัติการ","Operations"),
        "🌏 " + _t("สุขภาพประชากร","Population Health"),
        "🗺️ " + _t("ข้อมูล GIS","GIS Intelligence"),
        "📄 " + _t("รายงานประจำเดือน","Monthly Report"),
    ])

    with tab1: render_executive_tab(d)
    with tab2: render_operations_tab(d)
    with tab3: render_population_tab(d)
    with tab4: render_gis_tab(d)
    with tab5: render_monthly_report(d)
