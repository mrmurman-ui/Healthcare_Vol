"""Global Search V2.60 — Ctrl+K style search across all entities."""
from __future__ import annotations

import streamlit as st
from sqlalchemy import select, or_, text

from app.core.db_sync import get_sync_db


def search_all(query: str, limit: int = 30) -> dict[str, list[dict]]:
    """Fuzzy search across citizens, volunteers, households, tasks, referrals."""
    if not query or len(query.strip()) < 2:
        return {}

    q = query.strip().lower()
    results: dict[str, list[dict]] = {}

    try:
        with get_sync_db() as db:
            # Citizens
            try:
                from app.modules.citizens.model import Citizen
                rows = db.execute(
                    select(Citizen.id, Citizen.full_name,
                           Citizen.phone, Citizen.is_elderly)
                    .where(
                        or_(
                            Citizen.full_name.ilike(f"%{q}%"),
                            Citizen.phone.ilike(f"%{q}%"),
                        )
                    ).limit(10)
                ).all()
                if rows:
                    results["👤 Citizens"] = [
                        {"label": r[1], "sub": r[2] or "", "key": "citizens",
                         "tag": "👴 Elderly" if r[3] else "",
                         "id": str(r[0])}
                        for r in rows
                    ]
            except Exception:
                pass

            # Volunteers
            try:
                from app.modules.volunteers.model import Volunteer
                rows = db.execute(
                    select(Volunteer.id, Volunteer.full_name,
                           Volunteer.phone, Volunteer.district)
                    .where(
                        or_(
                            Volunteer.full_name.ilike(f"%{q}%"),
                            Volunteer.volunteer_code.ilike(f"%{q}%"),
                        )
                    ).limit(5)
                ).all()
                if rows:
                    results["🦺 Volunteers"] = [
                        {"label": r[1], "sub": r[3] or "", "key": "volunteers",
                         "tag": "", "id": str(r[0])}
                        for r in rows
                    ]
            except Exception:
                pass

            # Households
            try:
                from app.modules.households.model import Household
                rows = db.execute(
                    select(Household.id, Household.head_of_household,
                           Household.community, Household.household_code)
                    .where(
                        or_(
                            Household.head_of_household.ilike(f"%{q}%"),
                            Household.household_code.ilike(f"%{q}%"),
                            Household.community.ilike(f"%{q}%"),
                        )
                    ).limit(5)
                ).all()
                if rows:
                    results["🏘️ Households"] = [
                        {"label": r[1] or r[3], "sub": r[2] or "",
                         "key": "households", "tag": "", "id": str(r[0])}
                        for r in rows
                    ]
            except Exception:
                pass

            # Tasks
            try:
                from app.modules.tasks.model import Task
                rows = db.execute(
                    select(Task.id, Task.title, Task.status, Task.priority)
                    .where(
                        Task.title.ilike(f"%{q}%"),
                        Task.is_deleted == False,
                    ).limit(5)
                ).all()
                if rows:
                    results["✅ Tasks"] = [
                        {"label": r[1], "sub": f"{r[2]} · {r[3]}",
                         "key": "tasks", "tag": "", "id": str(r[0])}
                        for r in rows
                    ]
            except Exception:
                pass

            # Pages
            try:
                from app.modules.navigation.role_navigation_service import ALL_PAGES
                page_hits = [
                    {"label": p.label, "sub": p.label_th,
                     "key": p.key, "tag": p.icon, "id": ""}
                    for p in ALL_PAGES
                    if q in p.label.lower() or q in p.label_th.lower()
                ][:5]
                if page_hits:
                    results["📄 Pages"] = page_hits
            except Exception:
                pass

    except Exception:
        pass

    return results


def render_global_search() -> str | None:
    """Render global search bar. Returns selected page_key or None."""
    st.markdown("""
<style>
.search-wrap {
    position: relative; margin-bottom: 4px;
}
.search-shortcut {
    position: absolute; right: 10px; top: 50%;
    transform: translateY(-50%);
    font-size: 10px; color: #9CA3AF;
    background: #F3F4F6; border: 1px solid #E5E7EB;
    border-radius: 4px; padding: 2px 5px;
    pointer-events: none;
}
.search-result-group {
    font-size: 10px; font-weight: 700; color: #9CA3AF;
    text-transform: uppercase; letter-spacing: 1px;
    padding: 6px 8px 2px;
}
.search-result-item {
    display: flex; align-items: center; gap: 8px;
    padding: 8px 10px; border-radius: 8px; cursor: pointer;
    transition: background 0.15s;
}
.search-result-item:hover { background: #EFF6FF; }
.sr-label { font-size: 13px; font-weight: 600; color: #111827; }
.sr-sub { font-size: 11px; color: #6B7280; }
.sr-tag { font-size: 10px; color: #2563EB; }
</style>
""", unsafe_allow_html=True)

    query = st.text_input(
        "🔍",
        placeholder="ค้นหา ประชาชน อาสาสมัคร งาน หน้า... (Ctrl+K)",
        key="global_search_input",
        label_visibility="collapsed",
    )

    if not query or len(query.strip()) < 2:
        return None

    with st.spinner("Searching..."):
        results = search_all(query)

    if not results:
        st.caption("ไม่พบผลการค้นหา")
        return None

    total = sum(len(v) for v in results.values())
    st.caption(f"พบ {total} ผลลัพธ์")

    selected_key = None
    for group_label, items in results.items():
        st.markdown(f'<div class="search-result-group">{group_label}</div>',
                    unsafe_allow_html=True)
        for item in items:
            col1, col2 = st.columns([10, 1])
            with col1:
                st.markdown(
                    f'<div class="search-result-item">'
                    f'<span class="sr-tag">{item["tag"]}</span>'
                    f'<div><div class="sr-label">{item["label"]}</div>'
                    f'<div class="sr-sub">{item["sub"]}</div></div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with col2:
                if st.button("→", key=f"sr_{item['key']}_{item['id'][:8] if item['id'] else item['label'][:8]}"):
                    selected_key = item["key"]

    return selected_key
