from datetime import datetime, timedelta, timezone
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import json
import os

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def create_google_calendar_events(sessions):
    creds_info = json.loads(os.environ["GOOGLE_CREDENTIALS"])
    creds = Credentials.from_service_account_info(
        creds_info,
        scopes=SCOPES,
    )
    service = build(
        "calendar",
        "v3",
        credentials=creds,
    )
    calendar_id = os.getenv("CALENDAR_ID")
    schedule_date = datetime.today().date()
    created_events = []
    for session in sessions:
        start_time = str(session["start_time"])[:5]
        end_time = str(session["end_time"])[:5]

        start_dt = datetime.strptime(
            f"{schedule_date} {start_time}",
            "%Y-%m-%d %H:%M",
        )

        end_dt = datetime.strptime(
            f"{schedule_date} {end_time}",
            "%Y-%m-%d %H:%M",
        )

        event = {
            "summary": session.get(
                "calendar_title",
                f"Coaching Session - {session['student_id']}",
            ),
            "description": session.get("reason", ""),
            "start": {
                "dateTime": start_dt.isoformat(),
                "timeZone": "Asia/Kolkata",
            },
            "end": {
                "dateTime": end_dt.isoformat(),
                "timeZone": "Asia/Kolkata",
            },
        }

        created = (
            service.events()
            .insert(
                calendarId=calendar_id,
                body=event,
                sendUpdates="none",
            )
            .execute()
        )

        created_events.append(created["id"])

    return created_events


def get_today_coaching_events():
    creds_info = json.loads(os.environ["GOOGLE_CREDENTIALS"])

    creds = Credentials.from_service_account_info(
        creds_info,
        scopes=SCOPES,
    )

    service = build(
        "calendar",
        "v3",
        credentials=creds,
    )

    calendar_id = os.getenv("CALENDAR_ID")

    now = datetime.now(timezone.utc)

    start_of_day = now.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    end_of_day = start_of_day + timedelta(days=1)

    events_result = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=start_of_day.isoformat(),
            timeMax=end_of_day.isoformat(),
            singleEvents=True,
            orderBy="startTime",
            maxResults=100,
        )
        .execute()
    )

    events = events_result.get("items", [])

    sessions = []

    for event in events:
        start_raw = event.get("start", {}).get("dateTime")
        end_raw = event.get("end", {}).get("dateTime")

        if not start_raw or not end_raw:
            continue

        start_dt = datetime.fromisoformat(start_raw.replace("Z", "+00:00"))

        end_dt = datetime.fromisoformat(end_raw.replace("Z", "+00:00"))

        summary = event.get("summary", "")

        student_id = summary

        if summary.startswith("Coaching Session - "):
            student_id = summary.replace(
                "Coaching Session - ",
                "",
            )

        sessions.append(
            {
                "student_id": student_id,
                "session_type": "Coaching",
                "start_time": start_dt.strftime("%H:%M"),
                "end_time": end_dt.strftime("%H:%M"),
                "session_duration_minutes": int(
                    (end_dt - start_dt).total_seconds() / 60
                ),
                "reason": event.get("description", ""),
                "severity": "medium",
            }
        )

    return sessions
