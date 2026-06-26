import streamlit as st
from sqlalchemy import select

from app.core.db_sync import get_sync_db
from app.modules.localization.service import t
from app.modules.reports.service import generate_excel, generate_pdf
from app.modules.volunteers.model import Volunteer


def _t(th: str, en: str) -> str:
    import streamlit as _st
    return th if _st.session_state.get("lang", "TH") == "TH" else en


def render_reports() -> None:
    st.header(t("nav_reports"))

    report_type = st.selectbox(_t("เลือกรายงาน", "Select Report"), [
        t("rep_vol"), t("rep_hh"), t("rep_cit"), t("rep_vis"), t("rep_ref")
    ])

    col1, col2 = st.columns(2)
    export_pdf = col1.button(t("export_pdf"))
    export_excel_btn = col2.button(t("export_excel"))

    if export_pdf or export_excel_btn:
        with get_sync_db() as db:
            volunteers = db.execute(select(Volunteer).limit(500)).scalars().all()

        headers = [
            _t("รหัส", "Code"),
            _t("ชื่อ", "Name"),
            _t("จังหวัด", "Province"),
            _t("อำเภอ", "District"),
            _t("ตำแหน่ง", "Position"),
            _t("สถานะ", "Status"),
        ]
        rows = [
            [v.volunteer_code, v.full_name, v.province or "",
             v.district or "", v.position or "", v.status]
            for v in volunteers
        ]

        if export_pdf:
            data = generate_pdf(report_type, headers, rows)
            st.download_button(
                "⬇ " + _t("ดาวน์โหลด PDF", "Download PDF"),
                data, "report.pdf", "application/pdf"
            )
        else:
            data = generate_excel(report_type, headers, rows)
            st.download_button(
                "⬇ " + _t("ดาวน์โหลด Excel", "Download Excel"),
                data, "report.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
