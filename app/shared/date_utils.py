# -*- coding: utf-8 -*-
"""
Date utility functions for the MKI Community Health Platform.

Strategy:
  - DATABASE: always stores dates as YYYY-MM-DD (ISO/AD / ค.ศ.) — no changes needed.
  - DISPLAY (Thai mode): convert to DD/MM/YYYY with Buddhist Era year (พ.ศ. = AD + 543).
  - DISPLAY (EN mode): show as DD/MM/YYYY AD (no conversion).
  - INPUT: Streamlit date_input returns a Python `date` (AD) — we show the BE year
    in the field label as a hint and convert for display only.
  - DEMO DATA: all _rand_date() helper returns Python date objects stored as AD in DB;
    when displayed in Thai mode they are automatically shown as พ.ศ.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

import streamlit as st

BE_OFFSET = 543  # พ.ศ. = ค.ศ. + 543


# ── Core conversion helpers ──────────────────────────────────────────────────

def ad_to_be_year(year: int) -> int:
    """Convert AD year to Buddhist Era year."""
    return year + BE_OFFSET


def be_to_ad_year(year: int) -> int:
    """Convert Buddhist Era year to AD year."""
    return year - BE_OFFSET


def is_thai() -> bool:
    """Return True when the app is in Thai language mode."""
    return st.session_state.get("lang", "TH") == "TH"


# ── Format a date for display ────────────────────────────────────────────────

def fmt_date(d: Optional[date | str | datetime]) -> str:
    """
    Format a date for display:
      Thai mode  → DD/MM/YYYY (พ.ศ.)  e.g. 15/06/2569
      EN mode    → DD/MM/YYYY (ค.ศ.)  e.g. 15/06/2026
    Returns empty string if d is None/empty.
    """
    if d is None:
        return ""
    if isinstance(d, str):
        if not d.strip():
            return ""
        # Parse YYYY-MM-DD stored in DB
        try:
            d = datetime.strptime(d[:10], "%Y-%m-%d").date()
        except ValueError:
            return d  # return as-is if unparseable
    if isinstance(d, datetime):
        d = d.date()
    if not isinstance(d, date):
        return str(d)

    year = ad_to_be_year(d.year) if is_thai() else d.year
    return f"{d.day:02d}/{d.month:02d}/{year}"


def fmt_year(year: int) -> int:
    """Return the year in the current locale (BE for Thai, AD for EN)."""
    return ad_to_be_year(year) if is_thai() else year


def fmt_yearmonth(year: int, month: int) -> str:
    """Format a year-month label in current locale."""
    display_year = ad_to_be_year(year) if is_thai() else year
    return f"{display_year}/{month:02d}"


# ── Streamlit date_input wrapper ─────────────────────────────────────────────

def _t_local(th: str, en: str) -> str:
    """Local translation helper for date_utils."""
    try:
        return th if st.session_state.get("lang","TH")=="TH" else en
    except Exception:
        return th


def be_date_input(
    label: str,
    value: Optional[date] = None,
    key: Optional[str] = None,
    help: Optional[str] = None,
) -> Optional[date]:
    """
    Wrapper around st.date_input that shows พ.ศ. year hint and displays
    the selected date in DD/MM/YYYY พ.ศ. format below the input.
    Returns a Python date in AD for DB storage.
    """
    if value is None:
        from datetime import date as _date
        value = _date.today()

    if is_thai():
        display_label = label + " (ป้อนเป็น ค.ศ. — แสดงผลเป็น พ.ศ.)"
        _help = ((help or "") + " รูปแบบแสดงผล: DD/MM/YYYY พ.ศ.").strip()
    else:
        display_label = label
        _help = help

    kwargs = dict(label=display_label, value=value, format="DD/MM/YYYY")
    if key:
        kwargs["key"] = key
    if _help:
        kwargs["help"] = _help

    selected = st.date_input(**kwargs)

    if is_thai() and selected:
        be_y = ad_to_be_year(selected.year)
        st.caption(
            f"📅 {_t_local('วันที่เลือก','Selected')}: "
            f"**{selected.day:02d}/{selected.month:02d}/{be_y}** (พ.ศ.)"
        )

    return selected


def be_date_input_col(
    col,
    label: str,
    value: Optional[date] = None,
    key: Optional[str] = None,
) -> Optional[date]:
    """Same as be_date_input but renders into a Streamlit column."""
    if value is None:
        from datetime import date as _date
        value = _date.today()

    if is_thai():
        display_label = label + " (ค.ศ.→พ.ศ.)"
    else:
        display_label = label

    kwargs = dict(label=display_label, value=value, format="DD/MM/YYYY")
    if key:
        kwargs["key"] = key

    selected = col.date_input(**kwargs)

    if is_thai() and selected:
        be_y = ad_to_be_year(selected.year)
        col.caption(f"📅 {selected.day:02d}/{selected.month:02d}/{be_y} พ.ศ.")

    return selected


# ── Parse a BE date string entered by user ───────────────────────────────────

def parse_be_date(s: str) -> Optional[date]:
    """
    Parse a date string in DD/MM/YYYY format.
    If Thai mode: treats the year as พ.ศ. and converts to AD.
    If EN mode: treats as AD.
    Returns None if unparseable.
    """
    s = s.strip()
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            d = datetime.strptime(s, fmt).date()
            if is_thai() and fmt in ("%d/%m/%Y", "%d-%m-%Y"):
                d = d.replace(year=be_to_ad_year(d.year))
            return d
        except ValueError:
            continue
    return None


# ── Format a date string (from DB YYYY-MM-DD) for display ───────────────────

def fmt_db_date(s: Optional[str]) -> str:
    """
    Take a DB-stored date string (YYYY-MM-DD) and return display string.
    Thai mode: DD/MM/YYYY พ.ศ.
    EN mode:   DD/MM/YYYY
    """
    if not s:
        return ""
    return fmt_date(s)


# ── Year label helper ────────────────────────────────────────────────────────

def year_label() -> str:
    return "ปี (พ.ศ.)" if is_thai() else "Year"


def year_input(col, value: int, key: str = "year_sel") -> int:
    """
    Number input for year. Thai mode shows พ.ศ. and adds 543 to default.
    Returns the AD year (for DB use).
    """
    if is_thai():
        display_val = ad_to_be_year(value)
        be_val = col.number_input("ปี (พ.ศ.)", min_value=2563, max_value=2593,
                                   value=display_val, key=key)
        return be_to_ad_year(be_val)
    else:
        return col.number_input("Year", min_value=2020, max_value=2050,
                                 value=value, key=key)


# ── Chart axis label helpers ──────────────────────────────────────────────────
_THAI_MONTHS = ["","ม.ค.","ก.พ.","มี.ค.","เม.ย.","พ.ค.","มิ.ย.",
                "ก.ค.","ส.ค.","ก.ย.","ต.ค.","พ.ย.","ธ.ค."]


def be_month_label(ym_str: str) -> str:
    """Convert 'YYYY-MM' DB string to Thai พ.ศ. chart label.
    Thai: 'ม.ค. 2569'  EN: '2026-01'
    """
    try:
        y, m = int(str(ym_str)[:4]), int(str(ym_str)[5:7])
        if is_thai():
            return f"{_THAI_MONTHS[m]} {ad_to_be_year(y)}"
        return ym_str
    except Exception:
        return str(ym_str)


def be_year_label(year: int) -> str:
    """Return year as พ.ศ. in Thai mode, ค.ศ. in EN mode."""
    return str(ad_to_be_year(year)) if is_thai() else str(year)


def format_chart_months(month_list: list) -> list:
    """Convert a list of 'YYYY-MM' strings to Thai or EN labels for chart axes."""
    return [be_month_label(m) for m in month_list]
