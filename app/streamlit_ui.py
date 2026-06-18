import streamlit as st
from services.chat_service import chatResponse

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

STUDENT_ID = "STU001"
if user_prompt := st.chat_input("Ask Anything"):
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)
    with st.chat_message("assistant"):
        stream = chatResponse(user_prompt=user_prompt)
    response = st.write(stream)
    st.session_state.messages.append({"role": "assistant", "content": stream})
