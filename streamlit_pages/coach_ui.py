import json
from pathlib import Path
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv
from streamlit_calendar import calendar
from app.services.google_sheet_service import googleSheetData
from app.services.mem0_upload_service import call_llm
from app.services.google_calendar_service import create_google_calendar_events
from app.services.coach_chat_service import coachChatResponse
from app.prompts import COACH_DAILY_PLAN_PROMPT
from streamlit_autorefresh import st_autorefresh
from app.services.google_calendar_service import get_today_coaching_events

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")


@st.dialog("Student Brief", width="large")
def show_student_brief(student_id: str):

    if student_id not in st.session_state.brief_cache:
        with st.spinner("Retrieving memories and generating brief..."):
            brief = coachChatResponse(
                f"""
Generate a coaching brief for student {student_id}.

Use search_knowledge_base to retrieve information specifically for student_id={student_id}.

Use get_all_sheet_data to retrieve academic information for student_id={student_id}.

Use factual memories, session summaries, coaching signals and historical context for this student.

Return a concise coach-facing brief with the following sections:

## Current Situation
- Academic status
- Emotional status

## What's Changed
- Important developments since previous sessions

## Open Concerns
- Unresolved issues requiring follow-up

## Conversation Starters
- 3-4 specific questions the coach can use today

Requirements:
- Focus on recent information.
- Do not provide a full history dump.
- Use only information found for this student.
- If information is missing, say so.
"""
            )

            st.session_state.brief_cache[student_id] = brief

    st.markdown(st.session_state.brief_cache[student_id])

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "🔄 Refresh Brief",
            key=f"refresh_{student_id}",
            use_container_width=True,
        ):
            del st.session_state.brief_cache[student_id]
            st.rerun()

    with col2:
        if st.button(
            "❌ Close",
            key=f"close_{student_id}",
            use_container_width=True,
        ):
            st.rerun()


def render_severity_badge(severity) -> str:
    if isinstance(severity, int):
        if severity >= 9:
            severity = "critical"
        elif severity >= 7:
            severity = "high"
        elif severity >= 4:
            severity = "medium"
        else:
            severity = "low"

    styles = {
        "critical": {"bg": "#FEE2E2", "color": "#B91C1C", "label": "🔴 Critical"},
        "high": {"bg": "#FFEDD5", "color": "#C2410C", "label": "🟠 High"},
        "medium": {"bg": "#FEF9C3", "color": "#A16207", "label": "🟡 Medium"},
        "low": {"bg": "#DCFCE7", "color": "#15803D", "label": "🟢 Low"},
    }
    badge = styles.get(str(severity).lower(), styles["low"])
    return f"""
    <span style="
        background:{badge["bg"]};
        color:{badge["color"]};
        padding:4px 10px;
        border-radius:999px;
        font-size:0.8rem;
        font-weight:600;
        display:inline-block;
    ">{badge["label"]}</span>
    """


def student_card(session: dict) -> None:
    with st.container(border=True):
        col1, col2 = st.columns([4, 1])

        with col1:
            st.markdown(f"### Student {session['student_id']}")

            st.caption(
                f"{session['session_type']}  ·  "
                f"{session['start_time']} → {session['end_time']}  ·  "
                f"{session['session_duration_minutes']} min"
            )

            st.markdown(
                render_severity_badge(session["severity"]),
                unsafe_allow_html=True,
            )

            st.write(session["reason"])

        with col2:
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button(
                "Get Brief",
                key=f"brief_{session['student_id']}",
                use_container_width=True,
            ):
                show_student_brief(session["student_id"])


def deferred_card(student: dict) -> None:
    with st.container(border=True):
        col1, col2 = st.columns([1, 6])
        with col1:
            st.markdown("⏭️")
        with col2:
            st.markdown(f"**Student {student['student_id']}**")
            st.caption(student["reason"])


st.title("Coach Daily Planner")
if "plan" not in st.session_state:
    st.session_state.plan = None

if "active_brief" not in st.session_state:
    st.session_state.active_brief = None

if "plan_generated_at" not in st.session_state:
    st.session_state.plan_generated_at = None
if st.session_state.plan is None:
    existing_sessions = get_today_coaching_events()

    if existing_sessions:
        st.session_state.plan = {
            "summary": "Loaded from Google Calendar",
            "today": existing_sessions,
            "deferred": [],
            "changes": [],
            "conflicts": [],
            "coach_review_required": False,
        }
if st.session_state.plan:
    st_autorefresh(
        interval=300000,
        key="replan_checker",
    )
alerts = googleSheetData("replan_alerts")

new_alerts = []

if st.session_state.plan and st.session_state.plan_generated_at:
    plan_time = st.session_state.plan_generated_at
    new_alerts = [
        alert
        for alert in alerts
        if alert.get("processed", "No") == "No"
        and alert.get("created_at", "") > plan_time
    ]

if new_alerts:
    st.warning(f"{len(new_alerts)} student update(s) may affect the current plan.")

    with st.expander("View Updates", expanded=True):
        for alert in new_alerts:
            st.write(f"{alert['student_id']} - {alert['reason']}")


def is_actioned(row: dict) -> bool:
    val = (
        str(
            next(
                (v for k, v in row.items() if k.strip().lower() == "actioned"),
                "",
            )
        )
        .strip()
        .lower()
    )
    return val in ("yes", "true", "1", "y")


if new_alerts:
    if st.button(
        "Refresh Plan",
        type="primary",
        use_container_width=True,
    ):
        raw_signals = googleSheetData("signal_sheet")

        signals = [s for s in raw_signals if not is_actioned(s)]

        planner_input = {
            "signals": signals,
            "replan_alerts": new_alerts,
        }

        st.session_state.plan = call_llm(
            COACH_DAILY_PLAN_PROMPT,
            json.dumps(
                planner_input,
                indent=2,
                default=str,
            ),
        )

        st.session_state.plan_generated_at = datetime.now().isoformat()

        st.rerun()

if st.button("Generate My Day", type="primary", use_container_width=True):
    with st.spinner("Generating today's coaching plan..."):
        raw_signals = googleSheetData("signal_sheet")

        signals = [s for s in raw_signals if not is_actioned(s)]
        if not signals:
            st.warning("No pending signals found in the sheet.")
            st.stop()
        planner_input = {
            "signals": signals,
            "replan_alerts": [],
        }

        st.session_state.plan = call_llm(
            COACH_DAILY_PLAN_PROMPT,
            json.dumps(
                planner_input,
                indent=2,
                default=str,
            ),
        )

        st.session_state.plan_generated_at = datetime.now().isoformat()
        st.session_state.active_brief = None
        st.rerun()

if not st.session_state.plan:
    st.info("Click **Generate My Day** to build today's schedule.")
    st.stop()
plan = st.session_state.plan
if plan.get("summary"):
    st.info(plan["summary"])
today = plan.get("today", [])
deferred = plan.get("deferred", [])
changes = plan.get("changes", [])

if changes:
    st.subheader("Plan Changes")

    for change in changes:
        with st.container(border=True):
            st.write(f"{change['student_id']} - {change['change']}")
            st.caption(change["reason"])
st.subheader("Today's Schedule")
schedule_date = datetime.today().date()

events = []

for s in today:
    start_dt = datetime.strptime(f"{schedule_date} {s['start_time']}", "%Y-%m-%d %H:%M")

    end_dt = datetime.strptime(f"{schedule_date} {s['end_time']}", "%Y-%m-%d %H:%M")

    events.append(
        {
            "title": f"{s['student_id']} ({s['session_type']})",
            "start": start_dt.isoformat(),
            "end": end_dt.isoformat(),
        }
    )

if events:
    calendar(
        events=events,
        options={
            "initialView": "timeGridDay",
            "slotMinTime": "08:00:00",
            "slotMaxTime": "18:00:00",
            "height": 600,
        },
        key="coach_calendar",
    )
st.subheader(f"Today's Students — {len(today)}")

for session in today:
    student_card(session)

if deferred:
    st.subheader(f"Deferred to Tomorrow — {len(deferred)}")
    for student in deferred:
        deferred_card(student)
conflicts = plan.get("conflicts", [])

if conflicts:
    st.subheader("Coach Review Required")

    for conflict in conflicts:
        with st.container(border=True):
            st.write(f"{conflict['student_1']} vs {conflict['student_2']}")
            st.caption(conflict["reason"])

review_required = plan.get(
    "coach_review_required",
    False,
)

if review_required:
    st.warning("Coach review required before finalizing schedule.")

if today:
    st.divider()

    if st.button(
        "Confirm Plan",
        type="primary",
        use_container_width=True,
    ):
        create_google_calendar_events(today)

        st.success("Google Calendar events created successfully.")
