import streamlit as st
import uuid
from dotenv import load_dotenv
from defaults import DEFAULTS

load_dotenv()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "role" not in st.session_state:
    st.session_state.role = None

if "student_id" not in st.session_state:
    st.session_state.student_id = None

if "student_name" not in st.session_state:
    st.session_state.student_name = None

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "last_saved_index" not in st.session_state:
    st.session_state.last_saved_index = 0

if "session_summary_saved" not in st.session_state:
    st.session_state.session_summary_saved = False

if "quick_prompt" not in st.session_state:
    st.session_state.quick_prompt = None

if "brief_cache" not in st.session_state:
    st.session_state.brief_cache = {}
    st.session_state.active_brief = None

ROLES = [None, "Student", "Coach"]

student_chat_ui = st.Page("streamlit_pages/student_chat_ui.py", title="Chat UI")
coach_ui = st.Page("streamlit_pages/coach_ui.py", title="Coach UI")
coach_chat_ui = st.Page("streamlit_pages/coach_chat_ui.py", title="Coach Chat UI")


def login():
    st.header("Welcome!!")
    role = st.selectbox("Select your role", ROLES)
    if st.button("Log in"):
        st.session_state.role = role
        st.rerun()


def logout():
    for key, value in DEFAULTS.items():
        st.session_state[key] = value
    st.rerun()


student_details = st.Page(
    "streamlit_pages/student_details.py",
    title="Student Details",
    icon=":material/school:",
)
login_page = st.Page(login, title="Login", icon=":material/login:")
logout_page = st.Page(logout, title="Log out", icon=":material/logout:")
settings = st.Page(
    "streamlit_pages/settings.py", title="Settings", icon=":material/settings:"
)
account_pages = [logout_page, settings]

if st.session_state.role is None:
    pg = st.navigation([login_page])
elif st.session_state.role == "Student":
    if st.session_state.student_id is None:
        pg = st.navigation({"Profile": [student_details], "Account": [logout_page]})
    else:
        pg = st.navigation(
            {
                "Chat": [student_chat_ui],
                "Account": [settings, logout_page],
            }
        )
else:
    pg = st.navigation(
        {
            "Chat": [coach_ui, coach_chat_ui],
            "Account": [settings, logout_page],
        }
    )

pg.run()
