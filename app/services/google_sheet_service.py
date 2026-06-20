import streamlit as st
import gspread
import os
from google.oauth2.service_account import Credentials
from langchain.tools import tool
import json
from functools import lru_cache
from app.services.call_agent import merge_signals_with_llm
from app.services.replan_alerts import (
    build_alert_reason,
    create_replan_alert,
    should_create_replan_alert,
)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

creds_info = json.loads(os.environ["GOOGLE_CREDENTIALS"])
spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")


def get_sheets_client():
    try:
        creds = Credentials.from_service_account_info(
            creds_info,
            scopes=SCOPES,
        )
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Credentials Error: {e}")
        return None


def googleSheetData(sheet_name: str):
    """
    Retrieve all records from a Google Sheets worksheet.

    Args:
        sheet_name: Name of the worksheet/tab within the configured spreadsheet.
        Valid sheet_names are as follows: {"roster","exam_scores","attendance","exam_schedule","signal_sheet"}
    Returns:
        A list of dictionaries where each dictionary represents a row from
        the sheet and keys correspond to column headers.
    """
    client = get_sheets_client()
    if client is None:
        return {}
    try:
        spreadsheet = client.open_by_key(str(spreadsheet_id))
        worksheet = spreadsheet.worksheet(sheet_name)
        return worksheet.get_all_records()

    except Exception as e:
        st.error(f"Google Sheets Error: {e}")
        return {}


@lru_cache(maxsize=1)
def _cached_sheet_data():
    sheet_names = [
        "roster",
        "exam_scores",
        "attendance",
        "exam_schedule",
        "signal_sheet",
    ]

    return {sheet: googleSheetData(sheet) for sheet in sheet_names}


@tool
def get_all_sheet_data() -> str:
    """Retrieve all student operational data."""
    return json.dumps(_cached_sheet_data(), default=str)


@st.cache_resource
def googleStudentData(student_id: str):
    client = get_sheets_client()

    if client is None:
        return {}
    try:
        spreadsheet = client.open_by_key(str(spreadsheet_id))
        result = {}

        for worksheet in spreadsheet.worksheets():
            records = worksheet.get_all_records()

            if not records:
                continue

            matches = [
                row
                for row in records
                if str(row.get("student_id", "")).strip() == str(student_id).strip()
            ]

            if matches:
                result[worksheet.title] = matches

        return result

    except Exception as e:
        st.error(f"Google Sheets Error: {e}")
        return {}


def googleSummaryUpdate(summary):
    client = get_sheets_client()
    if client is None:
        return False
    try:
        spreadsheet = client.open_by_key(str(os.getenv("GOOGLE_SPREADSHEET_ID")))
        signal_sheet = spreadsheet.worksheet("signal_sheet")
        student_id = str(st.session_state.student_id)
        records = signal_sheet.get_all_records()
        existing_record = None
        row_number = None
        for idx, record in enumerate(records, start=2):
            if str(record.get("student_id")) == student_id:
                existing_record = record
                row_number = idx
                break
        if (
            existing_record
            and str(
                existing_record.get(
                    "actioned",
                    "No",
                )
            )
            .strip()
            .lower()
            == "no"
        ):
            final_signal = merge_signals_with_llm(
                existing_signal=existing_record,
                new_signal=summary,
            )
        else:
            final_signal = summary

        if existing_record:
            old_urgency = int(
                existing_record.get(
                    "urgency_score",
                    0,
                )
                or 0
            )

            old_severity = str(
                existing_record.get(
                    "severity",
                    "low",
                )
            )

            new_urgency = int(
                final_signal.get(
                    "urgency_score",
                    0,
                )
                or 0
            )

            new_severity = str(
                final_signal.get(
                    "severity",
                    "low",
                )
            )

            if should_create_replan_alert(
                old_urgency=old_urgency,
                new_urgency=new_urgency,
                old_severity=old_severity,
                new_severity=new_severity,
            ):
                create_replan_alert(
                    spreadsheet=spreadsheet,
                    student_id=student_id,
                    severity=final_signal.get("severity"),
                    urgency=final_signal.get("urgency"),
                    reason=build_alert_reason(
                        old_urgency=old_urgency,
                        new_urgency=new_urgency,
                        old_severity=old_severity,
                        new_severity=new_severity,
                    ),
                )

        row = [
            student_id,
            final_signal.get("signal_type"),
            final_signal.get("severity"),
            final_signal.get("severity_score"),
            final_signal.get("urgency"),
            final_signal.get("urgency_score"),
            final_signal.get("schedule_recommendation"),
            str(
                final_signal.get(
                    "coach_review_required",
                    False,
                )
            ),
            final_signal.get("reason"),
            final_signal.get("timestamp"),
            "No",
        ]
        if row_number:
            signal_sheet.update(
                range_name=f"A{row_number}:K{row_number}",
                values=[row],
            )
        else:
            signal_sheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"Google Sheets Error: {e}")
        return False
