import streamlit as st
from app.services.student_chat_service import chatResponse
from app.services.mem0_upload_service import auto_save_factual_memories, session_summary
from app.services.google_sheet_service import googleSummaryUpdate
from defaults import SESSION_DEFAULTS

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_prompt := st.chat_input("Ask Anything"):
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)
    with st.chat_message("assistant"):
        stream = chatResponse(user_prompt=user_prompt)
    response = st.write(stream)
    st.session_state.messages.append({"role": "assistant", "content": stream})
    auto_save_factual_memories()

with st.sidebar:
    st.header("End Session")

    if st.button("🧹 Clear Chat", use_container_width=True):
        summary = session_summary()
        googleSummaryUpdate(summary)
        for key, value in SESSION_DEFAULTS.items():
            st.session_state[key] = value
        st.rerun()
    st.divider()
