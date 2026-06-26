"""Unit tests — PDF and Excel report generation."""
import io

import openpyxl
import pytest

from app.modules.reports.service import generate_excel, generate_pdf


HEADERS = ["Code", "Name", "Status"]
ROWS = [
    ["VOL001", "สมชาย ใจดี", "active"],
    ["VOL002", "สมหญิง รักษ์ดี", "inactive"],
]


def test_generate_pdf_returns_bytes():
    result = generate_pdf("Test Report", HEADERS, ROWS)
    assert isinstance(result, bytes)
    assert len(result) > 100
    # PDF magic bytes
    assert result[:4] == b"%PDF"


def test_generate_pdf_non_empty_rows():
    result = generate_pdf("Empty", HEADERS, [])
    assert result[:4] == b"%PDF"


def test_generate_excel_returns_bytes():
    result = generate_excel("Test Report", HEADERS, ROWS)
    assert isinstance(result, bytes)


def test_generate_excel_readable():
    result = generate_excel("Volunteers", HEADERS, ROWS)
    wb = openpyxl.load_workbook(io.BytesIO(result))
    ws = wb.active
    # Header row
    header_row = [cell.value for cell in ws[1]]
    assert header_row == HEADERS
    # Data rows
    assert ws.cell(2, 1).value == "VOL001"
    assert ws.cell(3, 2).value == "สมหญิง รักษ์ดี"


def test_generate_excel_sheet_name_truncated():
    long_title = "A" * 50
    result = generate_excel(long_title, HEADERS, ROWS)
    wb = openpyxl.load_workbook(io.BytesIO(result))
    assert len(wb.active.title) <= 31
