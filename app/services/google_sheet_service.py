import streamlit as st
import gspread
import os
from google.oauth2.service_account import Credentials
import json

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


@st.cache_resource
def get_sheets_client():
    try:
        creds_info = json.loads(os.environ["GOOGLE_CREDENTIALS"])
        creds = Credentials.from_service_account_info(
            creds_info,
            scopes=SCOPES,
        )
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Credentials Error: {e}")
        return None


def googleSheetData(sheet_name: str):
    client = get_sheets_client()
    if client is None:
        return {}

    spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")

    try:
        spreadsheet = client.open_by_key(str(spreadsheet_id))
        worksheet = spreadsheet.worksheet(sheet_name)
        return worksheet.get_all_records()

    except Exception as e:
        st.error(f"Google Sheets Error: {e}")
        return {}


@st.cache_resource
def googleStudentData(student_id: str):
    client = get_sheets_client()

    if client is None:
        return {}

    spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")

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
    spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")
    try:
        spreadsheet = client.open_by_key(str(spreadsheet_id))
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
