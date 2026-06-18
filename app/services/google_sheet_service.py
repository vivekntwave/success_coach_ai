from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os
import json
from dotenv import load_dotenv

load_dotenv()

creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])


def googleSheetData(student_id: str):
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    flow = InstalledAppFlow.from_client_config(creds_dict, scopes=SCOPES)
    creds = flow.run_local_server(port=0)
    service = build("sheets", "v4", credentials=creds)

    SPREADSHEET_ID = os.getenv("GOOGLE_SPREADSHEET_ID")

    spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    result = {}

    for sheet in spreadsheet["sheets"]:
        sheet_name: str = sheet["properties"]["title"]
        values = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=SPREADSHEET_ID, range=sheet_name)
            .execute()
            .get("values", [])
        )
        if len(values) < 2:
            continue
        headers = values[0]
        if "student_id" not in headers:
            continue
        student_col = headers.index("student_id")
        matches = []
        for row in values[1:]:
            if len(row) <= student_col:
                continue

            if str(row[student_col]).strip() == str(student_id).strip():
                matches.append(
                    {
                        headers[i]: row[i] if i < len(row) else ""
                        for i in range(len(headers))
                    }
                )

        if matches:
            result[sheet_name] = matches
    return result
