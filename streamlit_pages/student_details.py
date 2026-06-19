import streamlit as st

student_id = st.text_input("Student ID")
student_name = st.text_input("Student Name")

if st.button("Save"):
    st.session_state.student_id = student_id
    st.session_state.student_name = student_name
    st.rerun()
