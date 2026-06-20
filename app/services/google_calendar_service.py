from datetime import datetime
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
