"""Report generation — PDF (Thai fonts) + Excel + HTML fallback."""
from __future__ import annotations

import io
import os
import sys
from datetime import datetime
from typing import Sequence

import openpyxl
from openpyxl.styles import Font as XFont, PatternFill, Alignment, Border, Side

# ── Thai font paths (searched in order) ──────────────────────────────────────
_THAI_FONT_SEARCH = [
    # Bundled with project
    os.path.join(os.path.dirname(__file__), "..", "..", "static", "fonts", "NotoSansThai-Regular.ttf"),
    os.path.join(os.path.dirname(__file__), "..", "..", "static", "fonts", "THSarabunNew.ttf"),
    # Windows system fonts
    r"C:\Windows\Fonts\THSarabunNew.ttf",
    r"C:\Windows\Fonts\TH_Sarabun_New.ttf",
    r"C:\Windows\Fonts\NotoSansThai-Regular.ttf",
    r"C:\Windows\Fonts\tahoma.ttf",        # partial Thai support
    # Linux
    "/usr/share/fonts/truetype/thai/TlwgTypist.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansThai-Regular.ttf",
    "/usr/share/fonts/truetype/fonts-tlwg/TlwgTypo.ttf",
    "/Library/Fonts/NotoSansThai-Regular.ttf",  # macOS
]

_THAI_BOLD_SEARCH = [
    os.path.join(os.path.dirname(__file__), "..", "..", "static", "fonts", "NotoSansThai-Bold.ttf"),
    os.path.join(os.path.dirname(__file__), "..", "..", "static", "fonts", "THSarabunNew Bold.ttf"),
    r"C:\Windows\Fonts\THSarabunNew Bold.ttf",
    r"C:\Windows\Fonts\NotoSansThai-Bold.ttf",
    "/usr/share/fonts/truetype/thai/TlwgTypist-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansThai-Bold.ttf",
]


def _find_font(paths: list[str]) -> str | None:
    for p in paths:
        p = os.path.normpath(os.path.abspath(p))
        if os.path.isfile(p):
            return p
    return None


def _register_thai_fonts():
    """Register Thai-capable fonts with ReportLab. Returns font name or None."""
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        reg  = _find_font(_THAI_FONT_SEARCH)
        bold = _find_font(_THAI_BOLD_SEARCH)

        if reg:
            pdfmetrics.registerFont(TTFont("ThaiFont", reg))
            if bold:
                pdfmetrics.registerFont(TTFont("ThaiFont-Bold", bold))
                from reportlab.pdfbase.pdfmetrics import registerFontFamily
                registerFontFamily("ThaiFont", normal="ThaiFont", bold="ThaiFont-Bold")
            else:
                from reportlab.pdfbase.pdfmetrics import registerFontFamily
                registerFontFamily("ThaiFont", normal="ThaiFont", bold="ThaiFont")
            return "ThaiFont", "ThaiFont-Bold" if bold else "ThaiFont"

        # Try Liberation Sans (no Thai, but won't crash)
        fallback = _find_font([
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            r"C:\Windows\Fonts\arial.ttf",
        ])
        if fallback:
            pdfmetrics.registerFont(TTFont("FallbackFont", fallback))
            return "FallbackFont", "FallbackFont"
    except Exception:
        pass
    return None, None


def generate_pdf(title: str, headers: list[str], rows: list[list]) -> bytes:
    """Generate Thai-capable PDF. Falls back to HTML bytes if no Thai font found."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        font_reg, font_bold = _register_thai_fonts()
        if font_reg is None:
            font_reg  = "Helvetica"
            font_bold = "Helvetica-Bold"

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4,
                                leftMargin=15*mm, rightMargin=15*mm,
                                topMargin=15*mm, bottomMargin=15*mm)

        title_style = ParagraphStyle(
            "ThaiTitle", fontName=font_bold, fontSize=16,
            spaceAfter=6, textColor=colors.HexColor("#1B3A6B"),
            encoding="utf-8",
        )
        sub_style = ParagraphStyle(
            "ThaiSub", fontName=font_reg, fontSize=10,
            spaceAfter=12, textColor=colors.grey,
        )
        cell_style = ParagraphStyle(
            "ThaiCell", fontName=font_reg, fontSize=9,
            leading=12, wordWrap="CJK",
        )

        elements = [
            Paragraph(title, title_style),
            Paragraph(
                f"วันที่สร้าง: {datetime.now().strftime('%d/%m/%Y %H:%M')}  |  "
                f"MKI Community Health Platform",
                sub_style
            ),
            Spacer(1, 6),
        ]

        # Build table with Paragraph cells (supports Thai wrapping)
        hdr_style = ParagraphStyle(
            "ThaiHdr", fontName=font_bold, fontSize=9,
            textColor=colors.white, alignment=1,
        )
        data = [[Paragraph(str(h), hdr_style) for h in headers]]
        for row in rows:
            data.append([Paragraph(str(cell), cell_style) for cell in row])

        usable_w = A4[0] - 30*mm
        col_w    = usable_w / max(len(headers), 1)

        tbl = Table(data, colWidths=[col_w] * len(headers), repeatRows=1)
        tbl.setStyle(TableStyle([
            ("BACKGROUND",   (0,0), (-1, 0),  colors.HexColor("#1B3A6B")),
            ("TEXTCOLOR",    (0,0), (-1, 0),  colors.white),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),  [colors.white, colors.HexColor("#F0F4F8")]),
            ("GRID",         (0,0), (-1,-1),  0.4, colors.HexColor("#CBD5E1")),
            ("VALIGN",       (0,0), (-1,-1),  "MIDDLE"),
            ("TOPPADDING",   (0,0), (-1,-1),  4),
            ("BOTTOMPADDING",(0,0), (-1,-1),  4),
            ("LEFTPADDING",  (0,0), (-1,-1),  5),
            ("RIGHTPADDING", (0,0), (-1,-1),  5),
        ]))

        elements.append(tbl)
        elements.append(Spacer(1,8))
        elements.append(Paragraph(
            f"© {datetime.now().year} MKI Supplies Co.,Ltd.  |  สงวนลิขสิทธิ์ทุกประการ",
            ParagraphStyle("Footer", fontName=font_reg, fontSize=8,
                           textColor=colors.grey, alignment=1)
        ))

        doc.build(elements)
        return buf.getvalue()

    except Exception as e:
        # Complete HTML fallback if PDF generation fails
        return _generate_html_fallback(title, headers, rows, str(e))


def _generate_html_fallback(title: str, headers: list[str],
                             rows: list[list], err: str = "") -> bytes:
    """Generate a UTF-8 HTML file when PDF fails — fully readable Thai."""
    note = f"<p style='color:orange;font-size:11px'>หมายเหตุ: ไม่พบฟอนต์ภาษาไทย ไฟล์นี้เป็น HTML แทน PDF ({err[:80]})</p>" if err else ""
    hdr_html = "".join(f"<th>{h}</th>" for h in headers)
    rows_html = ""
    for i,row in enumerate(rows):
        bg = "#f8faff" if i%2==0 else "#ffffff"
        cells = "".join(f"<td style='padding:5px 8px;border:1px solid #ddd'>{c}</td>" for c in row)
        rows_html += f"<tr style='background:{bg}'>{cells}</tr>"

    html = f"""<!DOCTYPE html>
<html lang="th"><head><meta charset="UTF-8">
<title>{title}</title>
<style>
  body{{font-family:'Noto Sans Thai','TH Sarabun New',Tahoma,Arial,sans-serif;
        font-size:13px;color:#222;padding:20px}}
  h1{{color:#1B3A6B;font-size:20px}}
  table{{border-collapse:collapse;width:100%;margin-top:12px}}
  th{{background:#1B3A6B;color:white;padding:7px 8px;text-align:left;font-size:12px}}
  .footer{{margin-top:20px;font-size:11px;color:#888;text-align:center}}
</style></head><body>
<h1>{title}</h1>
<p style="color:#666;font-size:12px">วันที่สร้าง: {datetime.now().strftime("%d/%m/%Y %H:%M")} | MKI Community Health Platform</p>
{note}
<table><thead><tr>{hdr_html}</tr></thead><tbody>{rows_html}</tbody></table>
<div class="footer">© {datetime.now().year} MKI Supplies Co.,Ltd. สงวนลิขสิทธิ์ทุกประการ</div>
</body></html>"""
    return html.encode("utf-8")


def generate_excel(title: str, headers: list[str], rows: list[list]) -> bytes:
    """Generate Excel with Thai font (Noto Sans Thai / TH Sarabun New)."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = (title[:31] if len(title) <= 31 else title[:28] + "...")

    THAI_FONT = "Noto Sans Thai"   # Windows will substitute if not installed
    FALLBACK  = "TH Sarabun New"

    # Title row
    ws.merge_cells(f"A1:{openpyxl.utils.get_column_letter(max(len(headers),1))}1")
    title_cell       = ws["A1"]
    title_cell.value = title
    title_cell.font  = XFont(name=THAI_FONT, bold=True, size=14,
                              color="1B3A6B")
    title_cell.alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[1].height = 24

    # Date row
    ws.merge_cells(f"A2:{openpyxl.utils.get_column_letter(max(len(headers),1))}2")
    ws["A2"].value = (f"วันที่สร้าง: {datetime.now().strftime('%d/%m/%Y %H:%M')} "
                      f"| MKI Community Health Platform")
    ws["A2"].font  = XFont(name=THAI_FONT, size=10, color="666666")
    ws.row_dimensions[2].height = 18

    # Header row
    hdr_fill = PatternFill(start_color="1B3A6B", end_color="1B3A6B", fill_type="solid")
    hdr_font = XFont(name=THAI_FONT, bold=True, size=11, color="FFFFFF")
    thin     = Side(style="thin", color="CBD5E1")
    border   = Border(left=thin, right=thin, top=thin, bottom=thin)

    for col_idx, hdr in enumerate(headers, start=1):
        cell           = ws.cell(row=3, column=col_idx, value=hdr)
        cell.fill      = hdr_fill
        cell.font      = hdr_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border    = border
    ws.row_dimensions[3].height = 20

    # Data rows
    even_fill = PatternFill(start_color="F0F4F8", end_color="F0F4F8", fill_type="solid")
    data_font = XFont(name=THAI_FONT, size=11)
    for row_idx, row in enumerate(rows, start=4):
        fill = even_fill if row_idx % 2 == 0 else None
        for col_idx, val in enumerate(row, start=1):
            cell           = ws.cell(row=row_idx, column=col_idx, value=str(val))
            cell.font      = data_font
            cell.alignment = Alignment(vertical="center", wrap_text=False)
            cell.border    = border
            if fill:
                cell.fill = fill
        ws.row_dimensions[row_idx].height = 16

    # Auto column width
    for col in ws.columns:
        max_len = 0
        col_letter = col[0].column_letter
        for cell in col:
            if cell.row < 3: continue  # skip title/date rows
            try:
                val_len = len(str(cell.value or ""))
                # Thai chars are wider — multiply by 1.5 for better fit
                max_len = max(max_len, val_len)
            except Exception:
                pass
        ws.column_dimensions[col_letter].width = min(max(max_len * 1.1 + 3, 10), 45)

    # Freeze header row
    ws.freeze_panes = "A4"

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
