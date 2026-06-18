import streamlit as st
from services.chat_service import chatResponse
from services.google_sheet_service import googleSheetData

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


if user_prompt := st.chat_input("Ask Anything"):
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)
    with st.chat_message("assistant"):
        stream = chatResponse(user_prompt=user_prompt)
        student_data = googleSheetData()
    response = st.write_stream(stream)
    st.write(student_data)
    st.session_state.messages.append({"role": "assistant", "content": stream})
