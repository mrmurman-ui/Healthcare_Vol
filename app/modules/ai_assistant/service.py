"""AI Community Assistant — supports OpenAI, Claude, Gemini."""
from __future__ import annotations

import streamlit as st
from sqlalchemy import func, select, text

from app.core.db_sync import get_sync_db
from app.modules.citizens.model import Citizen
from app.modules.home_visits.model import HomeVisit
from app.modules.localization.service import t
from app.modules.referrals.model import Referral
from app.modules.tasks.model import Task
from app.modules.volunteers.model import Volunteer

PROVIDERS = ["Claude (Anthropic)", "OpenAI", "Gemini"]

SUMMARY_TYPES = [
    "Weekly Summary",
    "Monthly Summary",
    "Community Summary",
    "Executive Summary",
    "Visit Summary",
    "Referral Summary",
    "Follow-Up Priority Recommendations",
    "Task Priority Recommendations",
    "Community Action Recommendations",
]

SYSTEM_PROMPT = """You are an AI assistant for a Community Health & Volunteer Operations Platform in Thailand.
You help community health officers, volunteers, and administrators understand community health data.

IMPORTANT RULES:
- You MUST NOT diagnose, suggest, or imply any medical diagnosis.
- You MUST NOT recommend specific medications or treatments.
- You CAN summarize operational data (visits, referrals, tasks).
- You CAN recommend follow-up priorities based on data patterns.
- You CAN suggest community action priorities.
- Always respond professionally and factually.
- Support both Thai and English.
- Be concise and actionable.
"""


def _get_community_stats(db) -> dict:
    """Gather community stats for AI context."""
    vol_count = db.execute(select(func.count()).select_from(Volunteer)).scalar() or 0
    cit_count = db.execute(select(func.count()).select_from(Citizen)).scalar() or 0
    visit_count = db.execute(select(func.count()).select_from(HomeVisit)).scalar() or 0
    ref_count = db.execute(select(func.count()).select_from(Referral)).scalar() or 0
    task_count = db.execute(
        select(func.count()).select_from(Task).where(Task.is_deleted == False)
    ).scalar() or 0

    overdue_tasks = db.execute(
        select(func.count()).select_from(Task).where(
            Task.status == "overdue", Task.is_deleted == False
        )
    ).scalar() or 0

    elderly_count = db.execute(
        select(func.count()).select_from(Citizen).where(Citizen.is_elderly == True)
    ).scalar() or 0

    pending_refs = db.execute(
        select(func.count()).select_from(Referral).where(
            Referral.status.in_(["pending", "in_progress"])
        )
    ).scalar() or 0

    # Recent visits (last 7 days)
    recent_visits = db.execute(text("""
        SELECT COUNT(*) FROM home_visits
        WHERE visit_date::date >= CURRENT_DATE - INTERVAL '7 days'
    """)).scalar() or 0

    return {
        "volunteers": vol_count,
        "citizens": cit_count,
        "home_visits_total": visit_count,
        "home_visits_last_7_days": recent_visits,
        "referrals_total": ref_count,
        "referrals_pending": pending_refs,
        "tasks_total": task_count,
        "tasks_overdue": overdue_tasks,
        "elderly_citizens": elderly_count,
    }


def _call_claude(prompt: str, api_key: str) -> str:
    import urllib.request, json
    payload = json.dumps({
        "model": "claude-sonnet-4-6",
        "max_tokens": 1000,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    return data["content"][0]["text"]


def _call_openai(prompt: str, api_key: str) -> str:
    import urllib.request, json
    payload = json.dumps({
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 1000,
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"]


def _call_gemini(prompt: str, api_key: str) -> str:
    import urllib.request, json
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
    payload = json.dumps({
        "contents": [{"parts": [{"text": SYSTEM_PROMPT + "\n\n" + prompt}]}]
    }).encode()
    req = urllib.request.Request(url, data=payload,
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    return data["candidates"][0]["content"]["parts"][0]["text"]


def call_ai(prompt: str, provider: str, api_key: str) -> str:
    try:
        if "Claude" in provider:
            return _call_claude(prompt, api_key)
        elif "OpenAI" in provider:
            return _call_openai(prompt, api_key)
        elif "Gemini" in provider:
            return _call_gemini(prompt, api_key)
    except Exception as e:
        return f"⚠️ AI Error: {e}"
    return "Provider not supported."


def render_ai_assistant() -> None:
    st.header("🤖 " + t("nav_ai_assistant"))

    # Provider config in sidebar area
    with st.expander("⚙️ AI Provider Settings", expanded=False):
        provider = st.selectbox("Provider", PROVIDERS)
        api_key = st.text_input("API Key", type="password",
                                 help="Enter your API key for the selected provider")
        st.caption("API key is used only for this session and never stored.")

    if not api_key:
        st.info("Enter your API key above to enable the AI assistant.")
        # Still show stats without AI
        with get_sync_db() as db:
            stats = _get_community_stats(db)
        st.subheader("Current Community Stats")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Volunteers", stats["volunteers"])
        c2.metric("Citizens", stats["citizens"])
        c3.metric("Visits (7d)", stats["home_visits_last_7_days"])
        c4.metric("Pending Referrals", stats["referrals_pending"])
        return

    # Summary type selection
    summary_type = st.selectbox("Select Summary Type", SUMMARY_TYPES)
    custom_question = st.text_area("Or ask a custom question (optional)",
                                    placeholder="e.g. Which areas need more volunteer coverage?")

    col1, col2 = st.columns([1, 4])
    generate = col1.button("🔮 Generate", type="primary")

    if generate:
        with get_sync_db() as db:
            stats = _get_community_stats(db)

        stats_text = "\n".join([f"- {k.replace('_', ' ').title()}: {v}"
                                 for k, v in stats.items()])

        if custom_question:
            prompt = f"""Community Health Platform Data:
{stats_text}

User Question: {custom_question}

Please provide a helpful, data-driven response."""
        else:
            prompt = f"""Generate a {summary_type} for a Community Health & Volunteer Operations Platform.

Current Community Data:
{stats_text}

Provide actionable insights and recommendations based on this data.
Do NOT include any medical diagnoses or treatment recommendations.
Focus on operational priorities, resource allocation, and community support needs."""

        with st.spinner("Generating AI response..."):
            response = call_ai(prompt, provider, api_key)

        st.subheader(f"📝 {summary_type}")
        st.markdown(response)

        # Download option
        st.download_button(
            "⬇ Download Summary",
            data=response,
            file_name=f"{summary_type.lower().replace(' ', '_')}.txt",
            mime="text/plain",
        )

    st.divider()

    # Always show live stats
    with get_sync_db() as db:
        stats = _get_community_stats(db)

    st.subheader("📊 Today's Dashboard")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Volunteers", stats["volunteers"])
    c2.metric("Citizens", stats["citizens"])
    c3.metric("Visits (7d)", stats["home_visits_last_7_days"])
    c4.metric("Pending Refs", stats["referrals_pending"])
    c5.metric("⚠️ Overdue Tasks", stats["tasks_overdue"],
              delta=None if stats["tasks_overdue"] == 0 else f"{stats['tasks_overdue']} overdue",
              delta_color="inverse")
