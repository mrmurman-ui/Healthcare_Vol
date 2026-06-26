# -*- coding: utf-8 -*-
"""MKI Login Page — components.html for left branding, pure Streamlit for right form."""
from __future__ import annotations
import os
from datetime import datetime, UTC
import streamlit as st
import streamlit.components.v1 as components
from sqlalchemy import select
from app.core.db_sync import get_sync_db
from app.core.security import verify_password
from app.modules.auth.session import login_user
from app.modules.users.model import User

_LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "mki_logo_b64.txt")
try:
    with open(_LOGO_PATH, encoding="utf-8") as _f:
        MKI_LOGO = _f.read().strip()
except Exception:
    MKI_LOGO = ""


def _record_login(username: str, user_id=None, success: bool = True) -> None:
    try:
        from app.modules.login_history.model import LoginHistory
        with get_sync_db() as db:
            db.add(LoginHistory(
                user_id=user_id, username=username,
                login_time=datetime.now(UTC),
                login_result="success" if success else "failed",
                failed_attempts=0 if success else 1,
                created_by="system", updated_by="system",
            ))
    except Exception:
        pass


def render_login() -> None:
    if "login_lang" not in st.session_state:
        st.session_state["login_lang"] = "TH"
    is_thai = st.session_state.get("login_lang", "TH") == "TH"

    # Global page CSS — safe, no class references that could fail
    st.markdown("""
<style>
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display:none !important; }

.stApp {
    background: linear-gradient(145deg,#E8F3FF 0%,#CCDFFE 25%,#B8D4FF 55%,#9BBFFF 100%) !important;
    min-height:100vh;
}
.main .block-container {
    padding-top:16px !important;
    padding-bottom:20px !important;
    max-width:100% !important;
}

/* Lang button */
[data-testid="stButton"] > button {
    background:rgba(255,255,255,0.88) !important;
    border:1.5px solid #BFDBFE !important;
    border-radius:20px !important;
    color:#1E40AF !important;
    font-size:13px !important;
    font-weight:600 !important;
    padding:5px 16px !important;
    height:auto !important;
}

/* Sign-In — dark navy gradient */
[data-testid="stButton"] > button[kind="primary"] {
    background:linear-gradient(135deg,#0B1B5E 0%,#1a3ab8 45%,#2563EB 100%) !important;
    color:#fff !important;
    border:none !important;
    border-radius:12px !important;
    height:52px !important;
    font-size:15px !important;
    font-weight:700 !important;
    width:100% !important;
    box-shadow:0 6px 24px rgba(11,27,94,0.5),inset 0 1px 0 rgba(255,255,255,0.15) !important;
    letter-spacing:0.3px !important;
}
[data-testid="stButton"] > button[kind="primary"]:hover {
    background:linear-gradient(135deg,#07134A 0%,#162f9e 45%,#1D4ED8 100%) !important;
    box-shadow:0 10px 30px rgba(11,27,94,0.6) !important;
    transform:translateY(-1px) !important;
}

/* Form inputs */
.stTextInput input {
    border:1.5px solid #BFDBFE !important;
    border-radius:10px !important;
    height:48px !important;
    font-size:14px !important;
    background:rgba(255,255,255,0.85) !important;
    color:#1F2937 !important;
    backdrop-filter:blur(8px) !important;
}
.stTextInput input:focus {
    border-color:#2563EB !important;
    background:#fff !important;
    box-shadow:0 0 0 3px rgba(37,99,235,0.12) !important;
}
.stTextInput label {
    font-size:13px !important;
    font-weight:600 !important;
    color:#374151 !important;
}
.stCheckbox label { font-size:13px !important; color:#6B7280 !important; }
</style>
""", unsafe_allow_html=True)

    # Language toggle — top right
    _, lc = st.columns([11, 1])
    with lc:
        if st.button("🌐 EN" if is_thai else "🌐 TH", key="ll"):
            st.session_state["login_lang"] = "EN" if is_thai else "TH"
            st.rerun()

    left_col, right_col = st.columns([1.2, 1])

    # ── LEFT: branding via self-contained iframe (components.html) ─────────────
    with left_col:
        t1   = "AI สุขภาพชุมชน &" if is_thai else "AI Community Health &"
        t2   = "ระบบอาสาสมัคร" if is_thai else "Volunteer Operations"
        sub  = ("แพลตฟอร์มบริหารจัดการสุขภาพชุมชน<br>เพื่อคุณภาพชีวิตที่ดีของทุกคน"
                if is_thai else
                "Community Health Management Platform<br>for Better Quality of Life")
        icons = ["🛡️","📊","👥","❤️"]
        fn    = (["ปลอดภัย","อัจฉริยะ","ชุมชน","ใส่ใจสุขภาพ"]
                 if is_thai else ["Secure","Intelligent","Community","Health Care"])
        sn    = ["Secure","Intelligent","Community","Health Care"]
        feats = "".join([f"""
<div style="text-align:center;min-width:72px;">
  <div style="width:52px;height:52px;background:rgba(255,255,255,0.9);
    border-radius:14px;display:inline-flex;align-items:center;justify-content:center;
    font-size:24px;margin-bottom:6px;box-shadow:0 3px 12px rgba(37,99,235,0.12);
    border:1px solid rgba(191,219,254,0.8);">{icons[i]}</div>
  <div style="font-size:12px;font-weight:700;color:#1E3A8A;">{fn[i]}</div>
  <div style="font-size:10px;color:#4B6CB7;">{sn[i]}</div>
</div>""" for i in range(4)])

        logo_html = (
            f'<img src="{MKI_LOGO}" style="width:88px;height:88px;object-fit:contain;">'
            if MKI_LOGO else '<span style="font-size:52px;">🏥</span>'
        )

        # ALL styling self-contained inside this HTML — never leaks to parent
        components.html(f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box;
       font-family:'Noto Sans Thai','Noto Sans',-apple-system,sans-serif; }}
  html,body {{ width:100%; height:100%; background:transparent; overflow:hidden; }}
  .wrap {{
    padding:32px 28px 28px 36px;
    position:relative;
    overflow:hidden;
    min-height:620px;
  }}
  .content {{ position:relative; z-index:2; }}
  .logo-box {{
    width:88px; height:88px;
    background:rgba(255,255,255,0.85);
    border-radius:16px;
    border:1px solid rgba(191,219,254,0.7);
    display:inline-flex; align-items:center; justify-content:center;
    box-shadow:0 4px 16px rgba(37,99,235,0.15);
    backdrop-filter:blur(10px);
    overflow:hidden;
    margin-bottom:16px;
  }}
  .brand-name {{
    font-size:24px; font-weight:800; color:#1E3A8A; line-height:1;
  }}
  .brand-cat {{
    font-size:10px; font-weight:700; color:#3B82F6;
    letter-spacing:3px; text-transform:uppercase; margin-top:4px;
  }}
  .divider {{
    width:44px; height:2px;
    background:linear-gradient(90deg,#2563EB,#60A5FA);
    border-radius:2px; margin:12px 0 24px;
  }}
  .title {{
    font-size:28px; font-weight:800; color:#1E3A8A;
    line-height:1.3; margin-bottom:10px;
  }}
  .subtitle {{
    font-size:14px; color:#2563EB; line-height:1.8; margin-bottom:32px;
  }}
  .feats {{ display:flex; gap:20px; flex-wrap:wrap; }}
</style>
</head>
<body>
<div class="wrap">

  <!-- Wave SVG background -->
  <svg style="position:absolute;top:0;left:0;width:100%;height:100%;z-index:0;pointer-events:none;"
       viewBox="0 0 600 650" xmlns="http://www.w3.org/2000/svg"
       preserveAspectRatio="xMidYMid slice">
    <path fill="rgba(37,99,235,0.10)"
      d="M-20,110 C130,52 295,178 468,115 C548,87 588,130 620,110 L620,0 L-20,0 Z"/>
    <path fill="none" stroke="#3B82F6" stroke-width="1.5" stroke-opacity="0.15"
      d="M-20,268 C92,220 258,312 428,254 C516,220 574,260 620,240"/>
    <path fill="none" stroke="#60A5FA" stroke-width="1" stroke-opacity="0.1"
      d="M-20,318 C138,288 302,365 472,310 C548,280 590,316 620,296"/>
    <text x="330" y="510" font-size="195" font-weight="900" fill="#1D4ED8"
      fill-opacity="0.04" font-family="Arial" letter-spacing="-4">MKI</text>
    <path fill="rgba(37,99,235,0.08)"
      d="M-20,558 C188,512 390,602 580,548 L620,548 L620,650 L-20,650 Z"/>
  </svg>

  <!-- Content -->
  <div class="content">
    <div class="logo-box">{logo_html}</div>
    <div class="brand-name">MKI Supplies</div>
    <div class="brand-cat">Business Consultancy</div>
    <div class="divider"></div>
    <div class="title">{t1}<br>{t2}</div>
    <div class="subtitle">{sub}</div>
    <div class="feats">{feats}</div>
  </div>

</div>
</body>
</html>
""", height=640, scrolling=False)

    # ── RIGHT: login card — pure Streamlit ────────────────────────────────────
    with right_col:
        is_thai = st.session_state.get("login_lang", "TH") == "TH"
        welcome  = "ยินดีต้อนรับ" if is_thai else "Welcome Back"
        tagline  = "เข้าสู่ระบบเพื่อดำเนินการต่อ" if is_thai else "Sign in to continue"
        u_lbl    = "ชื่อผู้ใช้ หรือ อีเมล" if is_thai else "Username or Email"
        p_lbl    = "รหัสผ่าน" if is_thai else "Password"
        rem_lbl  = "จดจำฉัน" if is_thai else "Remember me"
        fgt_lbl  = "ลืมรหัสผ่าน?" if is_thai else "Forgot password?"
        btn_lbl  = "→ เข้าสู่ระบบ" if is_thai else "→ Sign In"
        or_lbl   = "หรือ" if is_thai else "or"
        sso_lbl  = "เข้าสู่ระบบด้วย SSO" if is_thai else "Sign in with SSO"
        copy_lbl = "© 2024 MKI Supplies Co., Ltd." + (" สงวนลิขสิทธิ์" if is_thai else "")
        b1 = "ปลอดภัย" if is_thai else "Secure"

        logo_circle = (
            f'<img src="{MKI_LOGO}" style="width:54px;height:54px;'
            f'object-fit:contain;border-radius:50%;">'
            if MKI_LOGO else "🏥"
        )

        # Card — glassmorphism via inline styles only (safe for st.markdown)
        st.markdown(f"""
<div style="
  background:rgba(255,255,255,0.80);
  backdrop-filter:blur(20px);
  -webkit-backdrop-filter:blur(20px);
  border-radius:22px 22px 0 0;
  border:1px solid rgba(255,255,255,0.72);
  border-bottom:none;
  padding:32px 32px 14px;
  box-shadow:0 8px 32px rgba(30,64,175,0.13),
             inset 0 1px 0 rgba(255,255,255,0.9);
  margin-top:28px;
  text-align:center;
">
  <div style="
    width:72px;height:72px;
    background:rgba(255,255,255,0.92);
    backdrop-filter:blur(14px);
    -webkit-backdrop-filter:blur(14px);
    border:2px solid rgba(191,219,254,0.75);
    border-radius:50%;
    display:inline-flex;align-items:center;justify-content:center;
    overflow:hidden;
    box-shadow:0 4px 18px rgba(37,99,235,0.15),
               inset 0 1px 0 rgba(255,255,255,0.85);
    margin-bottom:14px;
  ">{logo_circle}</div>
  <div style="font-size:24px;font-weight:800;color:#1E3A8A;margin-bottom:4px;">{welcome}</div>
  <div style="font-size:13px;color:#6B7280;">{tagline}</div>
</div>
<div style="
  background:rgba(255,255,255,0.80);
  backdrop-filter:blur(20px);
  -webkit-backdrop-filter:blur(20px);
  border-left:1px solid rgba(255,255,255,0.72);
  border-right:1px solid rgba(255,255,255,0.72);
  padding:4px 32px 0;
">
""", unsafe_allow_html=True)

        # Real Streamlit inputs
        username = st.text_input(u_lbl, placeholder="admin", key="mki_user")
        password = st.text_input(p_lbl, type="password",
                                  placeholder="••••••••", key="mki_pass")

        c1, c2 = st.columns([1, 1])
        with c1:
            st.checkbox(rem_lbl, key="mki_rem")
        with c2:
            st.markdown(
                f'<div style="text-align:right;padding-top:6px;">'
                f'<span style="font-size:12px;color:#2563EB;font-weight:600;">'
                f'{fgt_lbl}</span></div>',
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        sign_in = st.button(btn_lbl, key="mki_signin",
                             use_container_width=True, type="primary")

        # Bottom of card
        st.markdown(f"""
</div>
<div style="
  background:rgba(255,255,255,0.80);
  backdrop-filter:blur(20px);
  -webkit-backdrop-filter:blur(20px);
  border-radius:0 0 22px 22px;
  border:1px solid rgba(255,255,255,0.72);
  border-top:none;
  padding:2px 32px 24px;
  box-shadow:0 20px 56px rgba(30,64,175,0.14),
             inset 0 -1px 0 rgba(255,255,255,0.6);
">
  <div style="display:flex;align-items:center;gap:12px;
    margin:14px 0 12px;color:#D1D5DB;font-size:12px;">
    <div style="flex:1;height:1px;background:rgba(229,231,235,0.6);"></div>
    <span style="color:#9CA3AF;">{or_lbl}</span>
    <div style="flex:1;height:1px;background:rgba(229,231,235,0.6);"></div>
  </div>
  <button style="width:100%;padding:13px;
    background:rgba(255,255,255,0.65);
    backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);
    color:#1E40AF;
    border:1.5px solid rgba(191,219,254,0.8);
    border-radius:10px;font-size:14px;font-weight:600;
    cursor:pointer;
    box-shadow:0 2px 8px rgba(37,99,235,0.08);">
    🏢 {sso_lbl}
  </button>
</div>

<!-- Footer -->
<div style="text-align:center;margin-top:14px;padding:0 16px;">
  <div style="font-size:11px;color:#4B6CB7;margin-bottom:6px;">{copy_lbl}</div>
  <div style="display:flex;justify-content:center;gap:16px;">
    <span style="font-size:11px;color:#4B6CB7;">🛡️ {b1}</span>
    <span style="font-size:11px;color:#4B6CB7;">🔒 PDPA</span>
    <span style="font-size:11px;color:#4B6CB7;">🔐 256-bit</span>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── Auth logic ─────────────────────────────────────────────────────────────
    if sign_in:
        if not username or not password:
            st.error("⚠️ " + ("กรุณากรอกชื่อผู้ใช้และรหัสผ่าน"
                               if is_thai else "Please enter username and password."))
            return
        with st.spinner("กำลังตรวจสอบ..." if is_thai else "Authenticating..."):
            user = None
            try:
                with get_sync_db() as db:
                    result = db.execute(
                        select(User).where(
                            User.email == username.strip().lower()
                        )
                    ).scalar_one_or_none()
                    if result and result.is_active and verify_password(
                        password, result.hashed_password
                    ):
                        user = result
                    elif result and not result.is_active:
                        st.error("🚫 " + ("บัญชีถูกปิดใช้งาน"
                                          if is_thai else "Account inactive."))
                        _record_login(username, success=False)
                        return
            except Exception as e:
                st.error(f"Database error: {e}")
                return
        if user:
            _record_login(username, user.id, success=True)
            st.success("✅ " + (f"ยินดีต้อนรับ {user.full_name}"
                                if is_thai else f"Welcome, {user.full_name}!"))
            login_user(user)
            st.rerun()
        else:
            _record_login(username, success=False)
            st.error("❌ " + ("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"
                               if is_thai else "Invalid username or password."))
