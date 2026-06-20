import json
from pathlib import Path
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv
from streamlit_calendar import calendar
from app.services.google_sheet_service import googleSheetData
from app.services.mem0_upload_service import call_llm
from app.services.google_calendar_service import create_google_calendar_events

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")

COACH_DAILY_PLAN_PROMPT = """
You are an AI coaching operations planner.

Your task is to build a complete coaching schedule for today.

Input:
A list of student signals.

Each signal contains:
- student_id
- signal_type
- severity
- urgency
- reason
- timestamp

Definitions:

Severity:
How serious the underlying issue is.

Urgency:
Whether the coach should act today or whether the issue can safely wait.

Scheduling Rules:

1. Prioritize urgency first.
2. Use severity as a secondary factor.
3. Students with crisis-level concerns should be scheduled first.
4. Create an efficient coaching day with minimal idle gaps.
5. Schedule only students that justify coach attention today.
6. Lower-priority students should be deferred.
7. Do not simply sort by score. Apply coaching judgment.
8. Every scheduled student must have a reason.

Assume:
- Coach workday starts at 09:00.
- Coach workday ends at 17:00.
- Lunch break: 13:00-14:00.
- Buffer between sessions: 5 minutes.

Duration Guidelines:
- Crisis: 45 minutes
- Follow-up: 30 minutes
- Check-in: 20 minutes

Return ONLY valid JSON.

{
  "today": [
    {
      "student_id": "",
      "session_type": "",
      "severity": "",
      "urgency": "",
      "session_duration_minutes": 0,
      "start_time": "",
      "end_time": "",
      "reason": "",
      "calendar_title": ""
    }
  ],
  "deferred": [
    {
      "student_id": "",
      "reason": ""
    }
  ]
}

Requirements:
- Generate a realistic schedule.
- No overlapping sessions.
- Respect working hours.
- Include exact start and end times.
- Keep reason under 20 words.
- calendar_title should be suitable for a Google Calendar event.
- Output JSON only.
"""


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
        st.markdown(f"### Student {session['student_id']}")

        st.caption(
            f"{session['session_type']}  ·  "
            f"{session['start_time']} → {session['end_time']}  ·  "
            f"{session['session_duration_minutes']} min"
        )

        st.markdown(render_severity_badge(session["severity"]), unsafe_allow_html=True)

        st.write(session["reason"])


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

if st.button("Generate My Day", type="primary", use_container_width=True):
    with st.spinner("Generating today's coaching plan..."):
        raw_signals = googleSheetData("signal_sheet")

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

        signals = [s for s in raw_signals if not is_actioned(s)]
        if not signals:
            st.warning("No pending signals found in the sheet.")
            st.stop()
        user_content = json.dumps(signals, indent=2, default=str)
        st.session_state.plan = call_llm(COACH_DAILY_PLAN_PROMPT, user_content)
        st.session_state.active_brief = None  # reset brief on new plan

if not st.session_state.plan:
    st.info("Click **Generate My Day** to build today's schedule.")
    st.stop()
plan = st.session_state.plan
today = plan.get("today", [])
deferred = plan.get("deferred", [])

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

if st.session_state.active_brief:
    student_id = st.session_state.active_brief
    st.divider()
    st.subheader(f"Brief — Student {student_id}")
    st.info(f"Brief for {student_id} will load here once memory retrieval is wired in.")
    if st.button("Close Brief"):
        st.session_state.active_brief = None

if deferred:
    st.subheader(f"Deferred to Tomorrow — {len(deferred)}")
    for student in deferred:
        deferred_card(student)

if today:
    st.divider()
    if st.button("Confirm Plan", type="primary", use_container_width=True):
        create_google_calendar_events(today)
