"""Shared CSS for all dashboard tabs."""
DASHBOARD_CSS = """
<style>
/* ── Power BI / Microsoft Fabric inspired ── */
.db-section-title {
    font-size: 13px; font-weight: 700; color: #1E3A8A;
    text-transform: uppercase; letter-spacing: 1.2px;
    padding: 14px 0 10px; border-bottom: 2px solid #EFF6FF;
    margin-bottom: 14px;
}
/* KPI cards */
.kpi-row { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 16px; }
.kpi { flex: 1; min-width: 120px; max-width: 180px;
    background: white; border-radius: 12px; padding: 14px 12px;
    border: 1px solid #E5E7EB; border-top: 3px solid #2563EB;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05); }
.kpi-red    { border-top-color: #DC2626; }
.kpi-amber  { border-top-color: #D97706; }
.kpi-green  { border-top-color: #059669; }
.kpi-purple { border-top-color: #7C3AED; }
.kpi-teal   { border-top-color: #0D9488; }
.kpi-icon { font-size: 20px; margin-bottom: 6px; }
.kpi-val { font-size: 26px; font-weight: 800; color: #111827; line-height: 1; }
.kpi-lbl { font-size: 11px; color: #6B7280; margin-top: 4px; }
.kpi-delta { font-size: 11px; margin-top: 5px; font-weight: 600; }
.dg { color: #059669; } .dr { color: #DC2626; } .da { color: #D97706; }
/* AI Summary card */
.ai-summary {
    background: linear-gradient(135deg, #EFF6FF 0%, #F5F3FF 100%);
    border: 1px solid #BFDBFE; border-left: 4px solid #2563EB;
    border-radius: 14px; padding: 20px 24px; margin-bottom: 16px;
    box-shadow: 0 4px 16px rgba(37,99,235,0.08);
}
.ai-header { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.ai-badge {
    background: linear-gradient(135deg,#2563EB,#7C3AED);
    color: white; font-size: 10px; font-weight: 700;
    padding: 3px 10px; border-radius: 20px; letter-spacing: 0.5px;
}
/* Alert badges */
.alert-strip { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }
.alert-badge {
    display: inline-flex; align-items: center; gap: 5px;
    font-size: 12px; font-weight: 600; padding: 6px 12px;
    border-radius: 20px;
}
.ab-crit { background: #FEF2F2; color: #DC2626; border: 1px solid #FECACA; }
.ab-high { background: #FFFBEB; color: #D97706; border: 1px solid #FDE68A; }
.ab-med  { background: #EFF6FF; color: #2563EB; border: 1px solid #BFDBFE; }
.ab-low  { background: #F0FDF4; color: #059669; border: 1px solid #BBF7D0; }
/* Scorecard table */
.sc-table { width:100%; border-collapse: collapse; font-size: 13px; }
.sc-table th { background: #F8FAFF; color: #374151; font-weight: 600;
    padding: 10px 12px; text-align: left; border-bottom: 2px solid #E5E7EB; }
.sc-table td { padding: 10px 12px; border-bottom: 1px solid #F3F4F6; }
.sc-table tr:hover td { background: #F8FAFF; }
.rank-1 { color: #D97706; font-weight: 800; }
.rank-2 { color: #6B7280; font-weight: 700; }
.rank-3 { color: #92400E; font-weight: 700; }
.score-bar { height: 6px; border-radius: 3px; background: #E5E7EB; overflow: hidden; }
.score-fill { height: 100%; border-radius: 3px; background: linear-gradient(90deg,#2563EB,#60A5FA); }
</style>
"""
