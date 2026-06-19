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


def googleSheetData(student_id: str):
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
