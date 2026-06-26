"""Import Engine — Excel, CSV, JSON with preview, validation, duplicate detection."""
from __future__ import annotations


def _t(th: str, en: str) -> str:
    import streamlit as _st
    return th if _st.session_state.get("lang","TH") == "TH" else en


import io
import json
from typing import Any

import pandas as pd
import streamlit as st

from app.core.db_sync import get_sync_db
from app.modules.auth.session import get_current_user
from app.modules.citizens.model import Citizen
from app.modules.households.model import Household
from app.modules.localization.service import t
from app.modules.volunteers.model import Volunteer
from app.shared.enums import Gender, HousingType, IncomeGroup, VolunteerStatus

IMPORT_TYPES = [_t("อาสาสมัคร","Volunteers"), _t("ครัวเรือน","Households"), _t("ประชาชน","Citizens")]

VOLUNTEER_COLUMNS = ["volunteer_code", "full_name", "phone", "province",
                     "district", "subdistrict", "village", "position"]
HOUSEHOLD_COLUMNS = ["household_code", "head_of_household", "address",
                     "village", "district", "province", "phone"]
CITIZEN_COLUMNS = ["full_name", "gender", "date_of_birth", "phone",
                   "occupation", "is_elderly", "is_disabled"]


def read_file(uploaded_file) -> pd.DataFrame | None:
    name = uploaded_file.name.lower()
    try:
        if name.endswith(".xlsx") or name.endswith(".xls"):
            return pd.read_excel(uploaded_file)
        elif name.endswith(".csv"):
            return pd.read_csv(uploaded_file)
        elif name.endswith(".json"):
            data = json.loads(uploaded_file.read())
            if isinstance(data, list):
                return pd.DataFrame(data)
            for key in data:
                if isinstance(data[key], list):
                    return pd.DataFrame(data[key])
        return None
    except Exception as e:
        st.error(f"File read error: {e}")
        return None


def validate_volunteers(df: pd.DataFrame) -> tuple[list[dict], list[str]]:
    errors = []
    valid = []
    for i, row in df.iterrows():
        code = str(row.get("volunteer_code", "")).strip()
        name = str(row.get("full_name", "")).strip()
        if not code:
            errors.append(f"Row {i+2}: Missing volunteer_code")
            continue
        if not name:
            errors.append(f"Row {i+2}: Missing full_name")
            continue
        valid.append({
            "volunteer_code": code,
            "full_name": name,
            "phone": str(row.get("phone", ""))[:15] if pd.notna(row.get("phone")) else None,
            "province": str(row.get("province", ""))[:100] if pd.notna(row.get("province")) else None,
            "district": str(row.get("district", ""))[:100] if pd.notna(row.get("district")) else None,
            "subdistrict": str(row.get("subdistrict", ""))[:100] if pd.notna(row.get("subdistrict")) else None,
            "village": str(row.get("village", ""))[:100] if pd.notna(row.get("village")) else None,
            "position": str(row.get("position", ""))[:100] if pd.notna(row.get("position")) else None,
            "status": VolunteerStatus.ACTIVE,
        })
    return valid, errors


def validate_citizens(df: pd.DataFrame) -> tuple[list[dict], list[str]]:
    errors = []
    valid = []
    for i, row in df.iterrows():
        name = str(row.get("full_name", "")).strip()
        if not name:
            errors.append(f"Row {i+2}: Missing full_name")
            continue
        gender = str(row.get("gender", "")).lower()
        if gender not in ("male", "female", "other", ""):
            gender = "other"
        valid.append({
            "full_name": name,
            "gender": gender or None,
            "phone": str(row.get("phone", ""))[:15] if pd.notna(row.get("phone")) else None,
            "occupation": str(row.get("occupation", ""))[:100] if pd.notna(row.get("occupation")) else None,
            "is_elderly": bool(row.get("is_elderly", False)),
            "is_disabled": bool(row.get("is_disabled", False)),
            "is_bedridden": bool(row.get("is_bedridden", False)),
            "is_pregnant": bool(row.get("is_pregnant", False)),
            "is_living_alone": bool(row.get("is_living_alone", False)),
        })
    return valid, errors


def import_volunteers(records: list[dict], actor: str) -> tuple[int, int]:
    imported = skipped = 0
    from sqlalchemy import select as sa_select
    for rec in records:
        try:
            with get_sync_db() as db:
                exists = db.execute(
                    sa_select(Volunteer).where(Volunteer.volunteer_code == rec["volunteer_code"])
                ).scalar_one_or_none()
                if exists:
                    skipped += 1
                    continue
                db.add(Volunteer(**rec, created_by=actor, updated_by=actor))
            imported += 1
        except Exception:
            skipped += 1
    return imported, skipped


def import_citizens(records: list[dict], actor: str) -> tuple[int, int]:
    imported = skipped = 0
    for rec in records:
        try:
            with get_sync_db() as db:
                db.add(Citizen(**rec, created_by=actor, updated_by=actor))
            imported += 1
        except Exception:
            skipped += 1
    return imported, skipped


def render_import_engine() -> None:
    st.header("📥 " + t("nav_import"))

    import_type = st.selectbox(_t("ประเภทการนำเข้า","Import Type"), IMPORT_TYPES)
    uploaded = st.file_uploader(
        f"Upload {import_type} File",
        type=["xlsx", "xls", "csv", "json"],
        help="Supported: Excel (.xlsx), CSV, JSON",
    )

    # Template download
    templates = {
        _t("อาสาสมัคร","Volunteers"): pd.DataFrame(columns=VOLUNTEER_COLUMNS),
        _t("ครัวเรือน","Households"): pd.DataFrame(columns=HOUSEHOLD_COLUMNS),
        _t("ประชาชน","Citizens"): pd.DataFrame(columns=CITIZEN_COLUMNS),
    }
    buf = io.BytesIO()
    templates[import_type].to_excel(buf, index=False)
    st.download_button(
        f"⬇ Download {import_type} Template",
        data=buf.getvalue(),
        file_name=f"{import_type.lower()}_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    if not uploaded:
        return

    df = read_file(uploaded)
    if df is None or df.empty:
        st.error("Could not read file or file is empty.")
        return

    st.subheader("Preview (first 10 rows)")
    st.dataframe(df.head(10), use_container_width=True)
    st.info(f"Total rows: {len(df)}")

    # Validate
    if import_type == _t("อาสาสมัคร","Volunteers"):
        valid, errors = validate_volunteers(df)
    elif import_type == _t("ประชาชน","Citizens"):
        valid, errors = validate_citizens(df)
    else:
        st.warning("Household import coming soon.")
        return

    col1, col2 = st.columns(2)
    col1.metric("Valid Records", len(valid))
    col2.metric("Validation Errors", len(errors))

    if errors:
        with st.expander("⚠️ Validation Errors"):
            for err in errors[:20]:
                st.write(f"- {err}")
            if len(errors) > 20:
                st.write(f"... and {len(errors) - 20} more")

    if valid and st.button(f"✅ Import {len(valid)} {import_type}", type="primary"):
        user = get_current_user()
        actor = user.email if user else "system"

        with st.spinner("Importing..."):
            if import_type == _t("อาสาสมัคร","Volunteers"):
                imported, skipped = import_volunteers(valid, actor)
            else:
                imported, skipped = import_citizens(valid, actor)

        st.success(f"✅ Imported: {imported}  |  ⏭️ Skipped (duplicates): {skipped}")
