"""Analytics module — charts and insights."""
from __future__ import annotations


def _t(th: str, en: str) -> str:
    import streamlit as _st
    return th if _st.session_state.get("lang","TH") == "TH" else en

import sqlalchemy as sa

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import func, select, text

from app.core.db_sync import get_sync_db
from app.modules.citizens.model import Citizen
from app.modules.home_visits.model import HomeVisit
from app.modules.localization.service import t
from app.modules.referrals.model import Referral
from app.modules.tasks.model import Task
from app.modules.volunteers.model import Volunteer
from app.shared.date_utils import be_month_label, format_chart_months


def render_analytics() -> None:
    st.header("📊 " + t("nav_analytics"))

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        _t("ผลการปฏิบัติงาน อสม.", "Volunteer Performance"),
        _t("แนวโน้มการเยี่ยมบ้าน", "Visit Trends"),
        _t("แนวโน้มการส่งต่อ", "Referral Trends"),
        _t("แนวโน้มงาน", "Task Trends"),
        _t("ประชากร", "Population"),
    ])

    with get_sync_db() as db:
        # Volunteer by status
        vol_rows = db.execute(
            select(Volunteer.status, func.count()).group_by(Volunteer.status)
        ).all()

        # Visits by month
        visit_rows = db.execute(text("""
            SELECT TO_CHAR(visit_date::date, 'YYYY-MM') as month, COUNT(*) as cnt
            FROM home_visits
            GROUP BY month ORDER BY month DESC LIMIT 12
        """)).fetchall()

        # Visits by vulnerability group per month (stacked bar)
        vuln_visit_rows = db.execute(text("""
            SELECT TO_CHAR(hv.visit_date::date, 'YYYY-MM') as month,
                   CASE
                     WHEN c.is_bedridden  = true THEN 'bedridden'
                     WHEN c.is_disabled   = true THEN 'disabled'
                     WHEN c.is_elderly    = true THEN 'elderly'
                     WHEN c.is_living_alone = true THEN 'alone'
                     WHEN c.is_pregnant   = true THEN 'pregnant'
                     ELSE 'general'
                   END as group_type,
                   COUNT(*) as cnt
            FROM home_visits hv
            LEFT JOIN citizens c ON c.id = hv.citizen_id
            GROUP BY month, group_type
            ORDER BY month DESC LIMIT 120
        """)).fetchall()

        # Referrals by status
        ref_rows = db.execute(
            select(Referral.status, func.count()).group_by(Referral.status)
        ).all()

        # Tasks by priority
        task_rows = db.execute(
            select(Task.priority, func.count())
            .where(Task.is_deleted == False)
            .group_by(Task.priority)
        ).all()

        # Citizen flags
        cit_row = db.execute(
            select(
                func.count().label("total"),
                func.sum(Citizen.is_elderly.cast(sa.Integer)).label("elderly"),
                func.sum(Citizen.is_disabled.cast(sa.Integer)).label("disabled"),
                func.sum(Citizen.is_bedridden.cast(sa.Integer)).label("bedridden"),
                func.sum(Citizen.is_pregnant.cast(sa.Integer)).label("pregnant"),
            )
        ).one()

        # Referrals by target
        ref_target_rows = db.execute(
            select(Referral.target, func.count()).group_by(Referral.target)
        ).all()

    # ── Tab 1: Volunteer Performance ──────────────────────────────────────────
    with tab1:
        col1, col2 = st.columns(2)
        if vol_rows:
            fig = px.pie(
                names=[r[0] for r in vol_rows],
                values=[r[1] for r in vol_rows],
                title=_t("อาสาสมัครตามสถานะ","Volunteers by Status"),
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            col1.plotly_chart(fig, use_container_width=True)

        # Visits per volunteer (top 10)
        with get_sync_db() as db2:
            top_vol = db2.execute(text("""
                SELECT v.full_name, COUNT(hv.id) as visits
                FROM volunteers v
                LEFT JOIN home_visits hv ON hv.volunteer_id = v.id
                GROUP BY v.id, v.full_name
                ORDER BY visits DESC LIMIT 10
            """)).fetchall()

        if top_vol:
            fig2 = px.bar(
                x=[r[0] for r in top_vol],
                y=[r[1] for r in top_vol],
                title=_t("อสม. 10 อันดับตามการเยี่ยมบ้าน","Top 10 Volunteers by Home Visits"),
                color_discrete_sequence=["#1e3a5f"],
            )
            col2.plotly_chart(fig2, use_container_width=True)

    # ── Tab 2: Visit Trends ───────────────────────────────────────────────────
    with tab2:
        is_th2 = st.session_state.get("lang","TH") == "TH"

        VULN_TH = {
            "elderly":  _t("ผู้สูงอายุ","Elderly"),
            "disabled": _t("ผู้พิการ","Disabled"),
            "bedridden":_t("ติดเตียง","Bedridden"),
            "alone":    _t("อยู่คนเดียว","Lives Alone"),
            "pregnant": _t("ตั้งครรภ์","Pregnant"),
            "general":  _t("ประชากรทั่วไป","General"),
        }
        VULN_COLORS = {
            "elderly":"#F97316","disabled":"#8B5CF6","bedridden":"#EF4444",
            "alone":"#3B82F6","pregnant":"#EC4899","general":"#D1D5DB",
        }
        VTYPE_TH = {
            "routine":      _t("ตามแผน","Routine"),
            "follow_up":    _t("ติดตาม","Follow-up"),
            "emergency":    _t("ฉุกเฉิน","Emergency"),
            "post_referral":_t("หลังส่งต่อ","Post-referral"),
        }

        # ── Row 1: Monthly bar + Visit type pie ──────────────────────────────
        r1c1, r1c2 = st.columns([2,1])

        if visit_rows:
            months_be = format_chart_months([r[0] for r in reversed(visit_rows)])
            counts_v  = [r[1] for r in reversed(visit_rows)]
            fig_bar = px.bar(
                x=months_be, y=counts_v,
                title=_t("การเยี่ยมบ้านรายเดือน (พ.ศ.)", "Monthly Home Visits (BE)"),
                color_discrete_sequence=["#1e3a5f"],
                text_auto=True,
            )
            fig_bar.update_layout(
                xaxis_title=_t("เดือน (พ.ศ.)","Month (BE)"),
                yaxis_title=_t("จำนวนการเยี่ยม","Visits"),
                paper_bgcolor="rgba(0,0,0,0)",
            )
            r1c1.plotly_chart(fig_bar, use_container_width=True)
        else:
            r1c1.info(_t("ยังไม่มีข้อมูลการเยี่ยมบ้าน","No visit data yet."))

        with get_sync_db() as db2:
            vtype_rows = db2.execute(
                select(HomeVisit.visit_type, func.count()).group_by(HomeVisit.visit_type)
            ).all()
        if vtype_rows:
            vt_labels = [VTYPE_TH.get(r[0],r[0]) for r in vtype_rows]
            fig_vtype = px.pie(
                names=vt_labels,
                values=[r[1] for r in vtype_rows],
                title=_t("การเยี่ยมบ้านตามประเภท","Visits by Type"),
                color_discrete_sequence=["#1e3a5f","#2563EB","#60A5FA","#93C5FD"],
                hole=0.4,
            )
            fig_vtype.update_traces(textinfo="percent+label")
            fig_vtype.update_layout(paper_bgcolor="rgba(0,0,0,0)",showlegend=False)
            r1c2.plotly_chart(fig_vtype, use_container_width=True)

        st.divider()

        # ── Row 2: Stacked bar — visits by vulnerability group per month ─────
        st.subheader("📊 " + _t("การเยี่ยมบ้านแยกตามกลุ่มเปราะบาง (รายเดือน)",
                                 "Home Visits by Vulnerability Group (Monthly)"))

        if vuln_visit_rows:
            import pandas as _pd
            # Build pivot: months × groups
            all_months_raw = sorted(set(r[0] for r in vuln_visit_rows))[-12:]
            all_months_be  = format_chart_months(all_months_raw)
            groups_order   = ["bedridden","disabled","elderly","alone","pregnant","general"]

            rows_dict = {g: [] for g in groups_order}
            for mraw in all_months_raw:
                month_data = {r[1]: r[2] for r in vuln_visit_rows if r[0]==mraw}
                for g in groups_order:
                    rows_dict[g].append(month_data.get(g, 0))

            fig_stack = go.Figure()
            for g in groups_order:
                if any(v > 0 for v in rows_dict[g]):
                    fig_stack.add_trace(go.Bar(
                        name=VULN_TH[g],
                        x=all_months_be,
                        y=rows_dict[g],
                        marker_color=VULN_COLORS[g],
                        text=[str(v) if v > 0 else "" for v in rows_dict[g]],
                        textposition="inside",
                        hovertemplate=f"{VULN_TH[g]}: %{{y:,}} {_t('ครั้ง','visits')}<extra></extra>",
                    ))

            fig_stack.update_layout(
                barmode="stack",
                title=_t("จำนวนการเยี่ยมบ้านแยกกลุ่มเปราะบางรายเดือน (พ.ศ.)",
                         "Monthly Visits by Vulnerability Group (BE)"),
                xaxis_title=_t("เดือน (พ.ศ.)","Month (BE)"),
                yaxis_title=_t("จำนวนครั้งการเยี่ยม","Number of Visits"),
                legend_title=_t("กลุ่มเปราะบาง","Group"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
                height=420,
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_stack, use_container_width=True)

            # ── Row 3: Percentage stacked (100%) ─────────────────────────────
            fig_pct = go.Figure()
            for g in groups_order:
                if any(v > 0 for v in rows_dict[g]):
                    # Compute %
                    totals = [sum(rows_dict[gg][i] for gg in groups_order)
                              for i in range(len(all_months_be))]
                    pcts = [round(rows_dict[g][i]/max(totals[i],1)*100,1)
                            for i in range(len(all_months_be))]
                    fig_pct.add_trace(go.Bar(
                        name=VULN_TH[g],
                        x=all_months_be,
                        y=pcts,
                        marker_color=VULN_COLORS[g],
                        hovertemplate=f"{VULN_TH[g]}: %{{y}}%<extra></extra>",
                    ))
            fig_pct.update_layout(
                barmode="relative",
                title=_t("สัดส่วนการเยี่ยมบ้านแยกกลุ่ม (% รายเดือน)",
                         "Visit Share by Group (% Monthly)"),
                xaxis_title=_t("เดือน (พ.ศ.)","Month (BE)"),
                yaxis_title=_t("สัดส่วน (%)","Share (%)"),
                yaxis=dict(ticksuffix="%", range=[0,100]),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
                legend_title=_t("กลุ่มเปราะบาง","Group"),
                height=360,
                showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_pct, use_container_width=True)

        else:
            st.info(_t("ยังไม่มีข้อมูลเพียงพอสำหรับกราฟกลุ่มเปราะบาง",
                       "Insufficient data for vulnerability breakdown chart."))

    # ── Tab 3: Referral Trends ────────────────────────────────────────────────
    with tab3:
        col1, col2 = st.columns(2)
        if ref_rows:
            fig = px.pie(
                names=[r[0] for r in ref_rows],
                values=[r[1] for r in ref_rows],
                title=_t("การส่งต่อตามสถานะ", "Referrals by Status"),
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            col1.plotly_chart(fig, use_container_width=True)

        if ref_target_rows:
            fig2 = px.bar(
                x=[r[0] for r in ref_target_rows],
                y=[r[1] for r in ref_target_rows],
                title=_t("การส่งต่อตามจุดหมาย", "Referrals by Target"),
                color_discrete_sequence=["#2e86ab"],
            )
            col2.plotly_chart(fig2, use_container_width=True)

    # ── Tab 4: Task Trends ────────────────────────────────────────────────────
    with tab4:
        try:
            PRIORITY_TH = {
                "critical": "🔴 " + _t("วิกฤต", "Critical"),
                "high":     "🟠 " + _t("สูง",   "High"),
                "medium":   "🟡 " + _t("ปานกลาง", "Medium"),
                "low":      "🟢 " + _t("ต่ำ",   "Low"),
            }
            STATUS_TH = {
                "new":         _t("ใหม่",              "New"),
                "assigned":    _t("มอบหมายแล้ว",       "Assigned"),
                "in_progress": _t("กำลังดำเนินการ",    "In Progress"),
                "completed":   _t("เสร็จสิ้น",         "Completed"),
                "overdue":     _t("เกินกำหนด",          "Overdue"),
                "cancelled":   _t("ยกเลิก",             "Cancelled"),
            }
            PRIORITY_COLORS = {
                "critical": "#DC2626", "high": "#F97316",
                "medium": "#EAB308", "low": "#22C55E",
            }

            col1, col2 = st.columns(2)

            if task_rows:
                is_th = st.session_state.get("lang", "TH") == "TH"
                p_labels = [PRIORITY_TH.get(r[0], r[0]) if is_th else r[0] for r in task_rows]
                p_values = [r[1] for r in task_rows]
                p_colors = [PRIORITY_COLORS.get(r[0], "#6B7280") for r in task_rows]
                fig = px.bar(
                    x=p_labels, y=p_values,
                    title=_t("งานตามระดับความสำคัญ", "Tasks by Priority"),
                    color=p_labels,
                    color_discrete_sequence=p_colors,
                    text_auto=True,
                )
                fig.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)")
                col1.plotly_chart(fig, use_container_width=True)
            else:
                col1.info(_t("ยังไม่มีข้อมูลงาน", "No task data yet."))

            with get_sync_db() as db2:
                tstatus_rows = db2.execute(
                    select(Task.status, func.count())
                    .where(Task.is_deleted == False)
                    .group_by(Task.status)
                ).all()

            if tstatus_rows:
                is_th = st.session_state.get("lang", "TH") == "TH"
                s_labels = [STATUS_TH.get(r[0], r[0]) if is_th else r[0] for r in tstatus_rows]
                fig2 = px.pie(
                    names=s_labels,
                    values=[r[1] for r in tstatus_rows],
                    title=_t("งานตามสถานะ", "Tasks by Status"),
                    color_discrete_sequence=px.colors.qualitative.Set2,
                    hole=0.4,
                )
                fig2.update_traces(textinfo="percent+label")
                fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)")
                col2.plotly_chart(fig2, use_container_width=True)
            else:
                col2.info(_t("ยังไม่มีข้อมูลสถานะงาน", "No task status data yet."))

            # Trend: tasks created over time
            with get_sync_db() as db3:
                task_trend = db3.execute(text("""
                    SELECT TO_CHAR(created_at, 'YYYY-MM') as month, COUNT(*) as cnt
                    FROM tasks
                    WHERE is_deleted = false
                    GROUP BY month ORDER BY month DESC LIMIT 12
                """)).fetchall()

            if task_trend:
                months = format_chart_months([r[0] for r in reversed(task_trend)])
                counts = [r[1] for r in reversed(task_trend)]
                fig3 = px.line(
                    x=months, y=counts, markers=True,
                    title=_t("แนวโน้มการสร้างงานรายเดือน", "Monthly Task Creation Trend"),
                    color_discrete_sequence=["#2563EB"],
                )
                fig3.update_layout(
                    xaxis_title=_t("เดือน", "Month"),
                    yaxis_title=_t("จำนวนงาน", "Tasks"),
                    paper_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig3, use_container_width=True)

        except Exception as e:
            st.error(_t(f"เกิดข้อผิดพลาด: {e}", f"Error loading task trends: {e}"))

    # ── Tab 5: Population ─────────────────────────────────────────────────────
    with tab5:
      try:
        total = int(cit_row.total or 0)
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric(_t("ประชาชนทั้งหมด", "Total Citizens"), total)
        c2.metric(_t("ผู้สูงอายุ", "Elderly"), int(cit_row.elderly or 0))
        c3.metric(_t("ผู้พิการ", "Disabled"), int(cit_row.disabled or 0))
        c4.metric(_t("ติดเตียง", "Bedridden"), int(cit_row.bedridden or 0))
        c5.metric(_t("ตั้งครรภ์", "Pregnant"), int(cit_row.pregnant or 0))

        if total:
            elderly  = int(cit_row.elderly  or 0)
            disabled = int(cit_row.disabled or 0)
            bedridden = int(cit_row.bedridden or 0)
            pregnant  = int(cit_row.pregnant or 0)

            flag_data = {
                _t("ผู้สูงอายุ", "Elderly"):  elderly,
                _t("ผู้พิการ",   "Disabled"): disabled,
                _t("ติดเตียง",  "Bedridden"): bedridden,
                _t("ตั้งครรภ์", "Pregnant"):  pregnant,
            }

            st.divider()
            st.subheader(_t("สัดส่วนกลุ่มเปราะบางต่อประชากรทั้งหมด",
                            "Vulnerability Categories as % of Total Population"))

            # ── Row 1: 4 donut gauges (one per category) ─────────────────────

            def _donut_gauge(label: str, count: int, total: int, color: str):
                pct = round(count / max(total, 1) * 100, 1)
                rest = 100 - pct
                fig = go.Figure(go.Pie(
                    values=[pct, rest],
                    labels=[label, ""],
                    hole=0.72,
                    marker_colors=[color, "#F3F4F6"],
                    textinfo="none",
                    hovertemplate=f"{label}: {count:,} คน ({pct}%)<extra></extra>",
                    showlegend=False,
                    sort=False,
                ))
                fig.update_layout(
                    height=220,
                    margin=dict(t=10, b=10, l=10, r=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    annotations=[dict(
                        text=f"<b>{pct}%</b><br><span style='font-size:11px'>{count:,} "
                             + _t("คน", "ppl") + "</span>",
                        x=0.5, y=0.5, showarrow=False,
                        font=dict(size=18, color=color),
                        xanchor="center", yanchor="middle",
                    )],
                )
                return fig

            COLORS = ["#F97316", "#8B5CF6", "#EF4444", "#EC4899"]
            labels_list = list(flag_data.keys())
            counts_list = list(flag_data.values())

            g_cols = st.columns(4)
            for idx, col in enumerate(g_cols):
                col.markdown(
                    f"<div style='text-align:center;font-weight:600;"
                    f"color:{COLORS[idx]};font-size:14px;margin-bottom:-10px'>"
                    f"{labels_list[idx]}</div>",
                    unsafe_allow_html=True,
                )
                col.plotly_chart(
                    _donut_gauge(labels_list[idx], counts_list[idx], total, COLORS[idx]),
                    use_container_width=True,
                )

            st.divider()

            # ── Row 2: stacked bar — population composition ────────────────
            col_a, col_b = st.columns(2)

            with col_a:
                # Pie: vulnerability categories vs general population
                other_count = total - sum(counts_list)
                pie_labels = labels_list + [_t("ประชากรทั่วไป", "General Population")]
                pie_values = counts_list + [max(other_count, 0)]
                pie_colors = COLORS + ["#D1D5DB"]
                fig_pie = px.pie(
                    names=pie_labels, values=pie_values,
                    title=_t("สัดส่วนกลุ่มเปราะบางในประชากร",
                             "Vulnerability Composition of Population"),
                    color_discrete_sequence=pie_colors,
                    hole=0.45,
                )
                fig_pie.update_traces(
                    textinfo="percent+label",
                    hovertemplate="%{label}: %{value:,} " + _t("คน", "people")
                                  + " (%{percent})<extra></extra>",
                )
                fig_pie.update_layout(
                    height=380,
                    margin=dict(t=50, b=20, l=10, r=10),
                    legend=dict(orientation="h", y=-0.15),
                    paper_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig_pie, use_container_width=True)

            with col_b:
                # Horizontal bar: count + % per category
                import pandas as _pd
                bar_df = _pd.DataFrame({
                    _t("หมวดหมู่", "Category"): labels_list,
                    _t("จำนวน", "Count"): counts_list,
                    _t("สัดส่วน %", "% of Population"): [
                        round(c / max(total, 1) * 100, 1) for c in counts_list
                    ],
                })
                fig_bar = px.bar(
                    bar_df,
                    x=_t("สัดส่วน %", "% of Population"),
                    y=_t("หมวดหมู่", "Category"),
                    orientation="h",
                    text=_t("สัดส่วน %", "% of Population"),
                    title=_t("เปอร์เซ็นต์ต่อประชากรทั้งหมด",
                             "% of Total Population per Category"),
                    color=_t("หมวดหมู่", "Category"),
                    color_discrete_sequence=COLORS,
                )
                fig_bar.update_traces(
                    texttemplate="%{text}%",
                    textposition="outside",
                )
                fig_bar.update_layout(
                    height=380,
                    margin=dict(t=50, b=20, l=10, r=50),
                    showlegend=False,
                    xaxis=dict(range=[0, max(
                        round(c / max(total,1)*100,1) for c in counts_list
                    ) * 1.25 if counts_list else 100]),
                    paper_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig_bar, use_container_width=True)

            # ── Bar chart: raw counts ─────────────────────────────────────
            fig_raw = px.bar(
                x=list(flag_data.keys()),
                y=list(flag_data.values()),
                title=_t("จำนวนประชาชนในแต่ละกลุ่มเปราะบาง",
                         "Vulnerability Flags Distribution (Count)"),
                color=list(flag_data.keys()),
                color_discrete_sequence=COLORS,
                text_auto=True,
            )
            fig_raw.update_layout(
                showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)",
                height=320,
            )
            st.plotly_chart(fig_raw, use_container_width=True)

        # Gender breakdown
        with get_sync_db() as db2:
            gender_rows = db2.execute(
                select(Citizen.gender, func.count()).group_by(Citizen.gender)
            ).all()
        if gender_rows:
            from app.shared.enum_labels import gender_labels as _gl
            _gmap = _gl()
            fig2 = px.pie(
                names=[_gmap.get(r[0] or "", _t("ไม่ระบุ", "unknown")) for r in gender_rows],
                values=[r[1] for r in gender_rows],
                title=_t("ประชาชนตามเพศ", "Citizens by Gender"),
                color_discrete_sequence=["#2563EB", "#EC4899", "#059669"],
                hole=0.4,
            )
            fig2.update_traces(textinfo="percent+label")
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True)
      except Exception as e:
          st.error(_t(f"เกิดข้อผิดพลาดในแท็บประชากร: {e}", f"Error loading population tab: {e}"))
