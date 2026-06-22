import streamlit as st

from app.services.google_sheet_service import googleStudentData
from app.services.mem0_retrieval_service import retrieve_profile_memories
from app.services.student_chat_service import build_system_prompt

student_id = st.text_input("Student ID")
student_name = st.text_input("Student Name")

if st.button("Save"):
    st.session_state.student_id = student_id
    st.session_state.student_name = student_name
    st.session_state.system_prompt = build_system_prompt(
        st.session_state.student_id, googleStudentData, retrieve_profile_memories
    )
    st.rerun()
