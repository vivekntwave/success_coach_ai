import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
from app.services.google_sheet_service import googleSheetData

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")
st.button("Generate my day")
st.button("Confirm Plan")

st.subheader("Today's Schedule")

students = googleSheetData("signal_sheet")


def render_severity_badge(severity: str):
    styles = {
        "critical": {"bg": "#FEE2E2", "color": "#B91C1C", "label": "🔴 Critical"},
        "high": {"bg": "#FFEDD5", "color": "#C2410C", "label": "🟠 High"},
        "medium": {"bg": "#FEF9C3", "color": "#A16207", "label": "🟡 Medium"},
        "low": {"bg": "#DCFCE7", "color": "#15803D", "label": "🟢 Low"},
    }

    badge = styles.get(severity.lower(), styles["low"])

    return f"""
    <span style="
        background:{badge["bg"]};
        color:{badge["color"]};
        padding:4px 10px;
        border-radius:999px;
        font-size:0.8rem;
        font-weight:600;
        display:inline-block;
    ">
        {badge["label"]}
    </span>
    """


def student_card(student):
    with st.container(border=True):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"### Student {student['student_id']}")
            st.caption(student["signal_type"])
            st.markdown(
                render_severity_badge(student["severity"]),
                unsafe_allow_html=True,
            )
            st.write(student["reason"])
            st.caption(student["timestamp"])
        with col2:
            if st.button(
                "Get Brief",
                key=f"brief_{student['student_id']}",
            ):
                st.success(f"Opening brief for Student {student['student_id']}")


st.subheader("Today's Students")

for student in students:
    student_card(student)
