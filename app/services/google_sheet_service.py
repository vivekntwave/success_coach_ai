import streamlit as st
import gspread
import os
from google.oauth2.service_account import Credentials
from langchain.tools import tool
import json
from functools import lru_cache

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
        worksheet = spreadsheet.worksheet("signal_sheet")
        student_id = str(st.session_state.student_id)
        records = worksheet.get_all_records()
        row_number = None
        for idx, record in enumerate(records, start=2):  # header is row 1
            if str(record["student_id"]) == student_id:
                row_number = idx
                break
        row = [
            student_id,
            str(summary["signal_type"]),
            str(summary["severity"]),
            str(summary["urgency"]),
            str(summary["reason"]),
            str(summary["timestamp"]),
            "No",
        ]
        if row_number:
            worksheet.update(range_name=f"A{row_number}:G{row_number}", values=[row])
        else:
            worksheet.append_row(row)

        return True

    except Exception as e:
        st.error(f"Google Sheets Error: {e}")
        return False
