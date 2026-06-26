"""User Management V2.60 — full CRUD, role assignment, scopes, login history."""
from __future__ import annotations
import secrets
import string
from datetime import datetime, UTC

import pandas as pd
import streamlit as st
from sqlalchemy import func, select, text

from app.core.db_sync import get_sync_db
from app.core.security import hash_password
from app.modules.auth.session import get_current_user
from app.modules.roles.model import ALL_ROLES, Role, UserRole
from app.modules.user_management.model import (
    ALL_STATUSES, USER_STATUS_ACTIVE, UserProfile,
)
from app.modules.user_scopes.model import UserScope
from app.modules.users.model import User


def _pw(length: int = 12) -> str:
    chars = string.ascii_letters + string.digits + "!@#$"
    return "".join(secrets.choice(chars) for _ in range(length))


def _legacy(role_code: str) -> str:
    m = {
        "SYSTEM_ADMIN": "super_admin", "PROVINCE_ADMIN": "province_admin",
        "DISTRICT_ADMIN": "district_admin", "SUBDISTRICT_ADMIN": "subdistrict_admin",
        "VOLUNTEER": "volunteer", "VIEWER": "viewer",
        "VOL_COORDINATOR": "volunteer", "COMMUNITY_LEADER": "viewer",
        "PHYSICIAN_ADVISOR": "viewer", "PUBLIC_HEALTH_OFFICER": "district_admin",
    }
    return m.get(role_code, "viewer")


def render_user_management() -> None:
    is_thai = st.session_state.get("lang", "TH") == "TH"

    # Seed roles — only once per session
    if "um_roles_seeded" not in st.session_state:
        try:
            from app.modules.permissions.service import seed_roles_and_permissions
            with get_sync_db() as db:
                seed_roles_and_permissions(db)
            st.session_state["um_roles_seeded"] = True
        except Exception:
            st.session_state["um_roles_seeded"] = True  # skip on error

    actor = get_current_user().email if get_current_user() else "admin"

    tab1, tab2, tab3, tab4 = st.tabs([
        "👥 " + ("รายชื่อผู้ใช้" if is_thai else "User List"),
        "➕ " + ("สร้างผู้ใช้" if is_thai else "Create User"),
        "🔑 " + ("บทบาทและสิทธิ์" if is_thai else "Roles & Permissions"),
        "📋 " + ("ประวัติการเข้าระบบ" if is_thai else "Login History"),
    ])

    # ── Tab 1: User List ──────────────────────────────────────────────────────
    with tab1:
        col1, col2, col3 = st.columns(3)
        search = col1.text_input("🔍 " + ("ค้นหา" if is_thai else "Search"), key="um_search")
        status_f = col2.selectbox("สถานะ" if is_thai else "Status",
                                   [""] + ["active","inactive"], key="um_status")
        role_f = col3.selectbox("บทบาท" if is_thai else "Role",
                                 [""] + [r[0] for r in ALL_ROLES], key="um_role")

        with get_sync_db() as db:
            try:
                stmt = select(User)
                if search:
                    stmt = stmt.where(
                        User.email.ilike(f"%{search}%") | User.full_name.ilike(f"%{search}%")
                    )
                if status_f == "active":
                    stmt = stmt.where(User.is_active == True)
                elif status_f == "inactive":
                    stmt = stmt.where(User.is_active == False)
                users = db.execute(stmt.limit(200)).scalars().all()
                total = db.execute(select(func.count()).select_from(User)).scalar() or 0
                active = db.execute(select(func.count()).select_from(User).where(User.is_active == True)).scalar() or 0
            except Exception as _e:
                st.error(f"Database error: {_e}")
                users = []; total = 0; active = 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("👥 " + ("ผู้ใช้ทั้งหมด" if is_thai else "Total Users"), total)
        c2.metric("✅ " + ("ใช้งาน" if is_thai else "Active"), active)
        c3.metric("❌ " + ("ปิดใช้งาน" if is_thai else "Inactive"), total - active)
        c4.metric("🎭 " + ("บทบาท" if is_thai else "Roles"), len(ALL_ROLES))

        st.divider()

        if users:
            df = pd.DataFrame([{
                "Email / Username": u.email,
                "ชื่อ-สกุล" if is_thai else "Full Name": u.full_name,
                "บทบาท" if is_thai else "Role": u.role,
                "จังหวัด" if is_thai else "Province": u.province or "-",
                "อำเภอ" if is_thai else "District": u.district or "-",
                "สถานะ" if is_thai else "Status": "✅ Active" if u.is_active else "❌ Inactive",
            } for u in users])
            st.dataframe(df, use_container_width=True, hide_index=True)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Export CSV", csv, "users.csv", "text/csv"
            )
        else:
            st.info("ไม่พบผู้ใช้งาน" if is_thai else "No users found.")

        # User actions
        st.divider()
        st.subheader("⚙️ " + ("จัดการผู้ใช้" if is_thai else "User Actions"))

        with get_sync_db() as db:
            all_users = db.execute(select(User)).scalars().all()
        opts = {f"{u.full_name} ({u.email})": str(u.id) for u in all_users}

        if opts:
            sel_label = st.selectbox(
                "เลือกผู้ใช้" if is_thai else "Select User", list(opts.keys())
            )
            sel_id = opts[sel_label]

            a1, a2, a3, a4 = st.columns(4)

            if a1.button("🔴 " + ("ปิดใช้งาน" if is_thai else "Deactivate"), use_container_width=True):
                try:
                    with get_sync_db() as db:
                        u = db.get(User, sel_id)
                        if u:
                            u.is_active = False
                            u.updated_by = actor
                    st.success("✅ " + ("ปิดใช้งานแล้ว" if is_thai else "User deactivated."))
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

            if a2.button("🟢 " + ("เปิดใช้งาน" if is_thai else "Reactivate"), use_container_width=True):
                with get_sync_db() as db:
                    u = db.get(User, sel_id)
                    if u:
                        u.is_active = True
                        u.updated_by = actor
                st.success("✅ " + ("เปิดใช้งานแล้ว" if is_thai else "User reactivated."))
                st.rerun()

            st.markdown("---")
            st.markdown("🔑 **" + ("จัดการรหัสผ่านผู้ใช้" if is_thai else "Manage User Password") + "**")
            pwd_col1, pwd_col2 = st.columns(2)
            admin_new_pwd = pwd_col1.text_input(
                ("รหัสผ่านใหม่ (กำหนดเอง)" if is_thai else "New Password (manual)"),
                type="password", key="admin_set_pwd",
                placeholder=("เว้นว่าง = สร้างอัตโนมัติ" if is_thai else "Blank = auto-generate"),
            )
            if pwd_col2.button("🔑 " + ("บันทึกรหัสผ่าน" if is_thai else "Set Password"), use_container_width=True, key="btn_set_pwd"):
                if admin_new_pwd.strip() and len(admin_new_pwd.strip()) < 6:
                    st.warning("⚠️ " + ("รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร" if is_thai else "Min 6 characters required."))
                else:
                    tmp = admin_new_pwd.strip() if admin_new_pwd.strip() else _pw(10)
                    with get_sync_db() as db:
                        u = db.get(User, sel_id)
                        if u:
                            u.hashed_password = hash_password(tmp)
                            u.updated_by = actor
                    if admin_new_pwd.strip():
                        st.success("✅ " + ("ตั้งรหัสผ่านใหม่สำเร็จแล้ว ผู้ใช้สามารถล็อกอินได้ทันที" if is_thai else "Password updated. User can log in immediately."))
                    else:
                        st.success(f"✅ " + ("รหัสผ่านชั่วคราว: " if is_thai else "Temp password: ") + f"`{tmp}` — " + ("แจ้งผู้ใช้งานทันที" if is_thai else "share securely."))

            with a4:
                new_role = st.selectbox("เปลี่ยนบทบาท" if is_thai else "Change Role",
                                         [r[0] for r in ALL_ROLES], key="um_change_role")
                if st.button("✔ " + ("บันทึก" if is_thai else "Apply"), use_container_width=True):
                    with get_sync_db() as db:
                        u = db.get(User, sel_id)
                        if u:
                            u.role = _legacy(new_role)
                            u.updated_by = actor
                    st.success(f"✅ Role → {new_role}")
                    st.rerun()

    # ── Tab 2: Create User ────────────────────────────────────────────────────
    with tab2:
        st.subheader("➕ " + ("สร้างผู้ใช้งานใหม่" if is_thai else "Create New User"))

        with st.form("create_user_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            email       = col1.text_input(("ชื่อผู้ใช้ / Email *" if is_thai else "Username / Email *"))
            full_name   = col2.text_input(("ชื่อ-สกุล *" if is_thai else "Full Name *"))
            first_th    = col1.text_input(("ชื่อ (ภาษาไทย)" if is_thai else "First Name (Thai)"))
            last_th     = col2.text_input(("นามสกุล (ภาษาไทย)" if is_thai else "Last Name (Thai)"))
            first_en    = col1.text_input(("ชื่อ (อังกฤษ)" if is_thai else "First Name (EN)"))
            last_en     = col2.text_input(("นามสกุล (อังกฤษ)" if is_thai else "Last Name (EN)"))
            phone       = col1.text_input(("เบอร์โทร" if is_thai else "Phone"))
            org         = col2.text_input(("องค์กร" if is_thai else "Organization"))
            position    = col1.text_input(("ตำแหน่ง" if is_thai else "Position"))
            vol_code    = col2.text_input(("รหัส อสม." if is_thai else "Volunteer Code"))
            role        = col1.selectbox(("บทบาท *" if is_thai else "Role *"), [r[0] for r in ALL_ROLES])
            province    = col2.text_input(("จังหวัด" if is_thai else "Province"))
            district    = col1.text_input(("อำเภอ" if is_thai else "District"))
            subdistrict = col2.text_input(("ตำบล" if is_thai else "Subdistrict"))
            st.markdown("---")
            st.markdown("🔑 **" + ("ตั้งค่ารหัสผ่าน" if is_thai else "Password Setup") + "**")
            pc1, pc2 = st.columns(2)
            auto_pwd    = pc1.checkbox(("สร้างรหัสผ่านอัตโนมัติ" if is_thai else "Auto-generate password"), value=True)
            # Always show manual password field — disabled only when auto is checked
            manual_pwd  = pc2.text_input(
                ("รหัสผ่าน (กรณีกำหนดเอง)" if is_thai else "Password (if manual)"),
                type="password",
                placeholder=("เว้นว่างเพื่อสร้างอัตโนมัติ" if is_thai else "Leave blank for auto"),
                disabled=auto_pwd,
            )
            submitted   = st.form_submit_button("➕ " + ("สร้างผู้ใช้" if is_thai else "Create User"),
                                                 type="primary", use_container_width=True)

        if submitted:
            if not email or not full_name:
                st.error("กรุณากรอก Username และ ชื่อ-สกุล" if is_thai else "Username and Full Name are required.")
            else:
                if auto_pwd:
                    pwd = _pw()
                elif manual_pwd and len(manual_pwd) >= 6:
                    pwd = manual_pwd
                else:
                    if not auto_pwd and not manual_pwd:
                        st.error("กรุณากรอกรหัสผ่าน" if is_thai else "Please enter a password (min 6 chars).")
                        pwd = None
                    else:
                        pwd = manual_pwd
                try:
                    # ── Step 1: Check duplicate & create core User (own transaction) ──
                    new_user_id = None
                    with get_sync_db() as db:
                        existing = db.execute(
                            select(User).where(User.email == email.strip().lower())
                        ).scalar_one_or_none()
                        if existing:
                            st.error("❌ Username นี้มีอยู่แล้ว" if is_thai else "❌ Username already exists.")
                            st.stop()
                        new_user = User(
                            email=email.strip().lower(),
                            hashed_password=hash_password(pwd),
                            full_name=full_name,
                            role=_legacy(role),
                            province=province or None,
                            district=district or None,
                            subdistrict=subdistrict or None,
                            is_active=True,
                            created_by=actor, updated_by=actor,
                        )
                        db.add(new_user)
                        db.flush()
                        new_user_id = str(new_user.id)
                    # User committed — login now works regardless of profile errors

                    # ── Step 2: UserProfile (separate transaction, non-fatal) ──────
                    try:
                        with get_sync_db() as db:
                            db.add(UserProfile(
                                user_id=new_user_id,
                                first_name_th=first_th or None,
                                last_name_th=last_th or None,
                                first_name_en=first_en or None,
                                last_name_en=last_en or None,
                                phone=phone or None,
                                organization=org or None,
                                position=position or None,
                                volunteer_code=vol_code or None,
                                status=USER_STATUS_ACTIVE,
                                force_password_change=auto_pwd,
                                created_by=actor, updated_by=actor,
                            ))
                    except Exception:
                        pass  # Profile is supplementary — user can still log in

                    # ── Step 3: UserScope (separate transaction, non-fatal) ─────────
                    if any([province, district, subdistrict]):
                        try:
                            with get_sync_db() as db:
                                db.add(UserScope(
                                    user_id=new_user_id,
                                    province_code=province or None,
                                    district_code=district or None,
                                    subdistrict_code=subdistrict or None,
                                    assigned_by=actor,
                                    created_by=actor, updated_by=actor,
                                ))
                        except Exception:
                            pass  # Scope is supplementary

                    st.success(f"✅ สร้างผู้ใช้งาน **{email}** สำเร็จ" if is_thai else f"✅ Created: **{email}**")
                    if auto_pwd:
                        st.info(
                            f"🔑 รหัสผ่านชั่วคราว: `{pwd}` — กรุณาแจ้งผู้ใช้งานและเปลี่ยนรหัสผ่านทันที"
                            if is_thai else
                            f"🔑 Temp password: `{pwd}` — share securely and ask user to change it."
                        )
                    st.rerun()
                except Exception as e:
                    st.error(f"{'เกิดข้อผิดพลาด' if is_thai else 'Error'}: {e}")

    # ── Tab 3: Roles & Permissions ────────────────────────────────────────────
    with tab3:
        st.subheader("🎭 " + ("บทบาทและสิทธิ์" if is_thai else "Roles & Permissions Matrix"))

        # Role list
        with get_sync_db() as db:
            try:
                roles = db.execute(
                    select(Role).where(Role.is_deleted == False)
                ).scalars().all()
                role_df = pd.DataFrame([{
                    "Code": r.role_code,
                    "ชื่อภาษาไทย" if is_thai else "Thai Name": r.role_name_th,
                    "English Name": r.role_name_en,
                } for r in roles])
            except Exception:
                role_df = pd.DataFrame([{
                    "Code": r[0],
                    "Thai Name": r[1],
                    "English Name": r[2],
                } for r in ALL_ROLES])

        st.dataframe(role_df, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("🗺️ " + ("สิทธิ์ตามบทบาท" if is_thai else "Permission Matrix by Role"))

        from app.modules.permissions.model import ROLE_PERMISSION_MATRIX, MODULES
        matrix_rows = []
        for role_code, module_actions in ROLE_PERMISSION_MATRIX.items():
            for mod in MODULES[:10]:
                acts = module_actions.get(mod, [])
                matrix_rows.append({
                    "Role": role_code,
                    "Module": mod,
                    "Permissions": ", ".join(acts) if acts else "—",
                })
        st.dataframe(pd.DataFrame(matrix_rows), use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("📍 " + ("มอบหมายพื้นที่" if is_thai else "Assign Area Scope"))
        with get_sync_db() as db:
            all_users2 = db.execute(select(User)).scalars().all()
        scope_opts = {f"{u.full_name} ({u.email})": str(u.id) for u in all_users2}

        with st.form("scope_form"):
            scope_user = st.selectbox("User", list(scope_opts.keys()))
            sc1, sc2, sc3, sc4 = st.columns(4)
            sp = sc1.text_input("Province Code")
            sd = sc2.text_input("District Code")
            ss = sc3.text_input("Subdistrict Code")
            sv = sc4.text_input("Village Code")
            scope_submit = st.form_submit_button("✔ " + ("บันทึก" if is_thai else "Assign"))

        if scope_submit:
            try:
                with get_sync_db() as db:
                    db.add(UserScope(
                        user_id=scope_opts[scope_user],
                        province_code=sp or None,
                        district_code=sd or None,
                        subdistrict_code=ss or None,
                        village_code=sv or None,
                        assigned_by=actor,
                        created_by=actor, updated_by=actor,
                    ))
                st.success("✅ " + ("บันทึกพื้นที่แล้ว" if is_thai else "Scope assigned."))
            except Exception as e:
                st.error(f"Error: {e}")

    # ── Tab 4: Login History ──────────────────────────────────────────────────
    with tab4:
        st.subheader("📋 " + ("ประวัติการเข้าระบบ" if is_thai else "Login History"))
        try:
            from app.modules.login_history.model import LoginHistory
            with get_sync_db() as db:
                logins = db.execute(
                    select(LoginHistory)
                    .order_by(LoginHistory.login_time.desc())
                    .limit(100)
                ).scalars().all()

            if logins:
                df_l = pd.DataFrame([{
                    "Username": l.username,
                    "เวลา" if is_thai else "Time": str(l.login_time or "")[:19],
                    "ผล" if is_thai else "Result": "✅" if l.login_result == "success" else "❌",
                    "ความพยายาม" if is_thai else "Attempts": l.failed_attempts,
                    "IP": l.ip_address or "-",
                } for l in logins])
                st.dataframe(df_l, use_container_width=True, hide_index=True)
            else:
                st.info("ยังไม่มีประวัติ" if is_thai else "No login history yet.")
        except Exception as e:
            st.error(f"Login history error: {e}")
