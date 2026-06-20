import streamlit as st
import traceback
from app.services.coach_chat_service import coachChatResponse


st.set_page_config(
    page_title="Coach Copilot",
    page_icon="🎓",
    layout="wide",
)

st.title("🎓 Coach Copilot")

st.subheader("Quick Actions")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("📄 Student Brief"):
        st.session_state.quick_prompt = (
            "Generate a complete student brief covering all students."
        )

with col2:
    if st.button("⚠️ Open Concerns"):
        st.session_state.quick_prompt = (
            "What student concerns currently require attention?"
        )

with col3:
    if st.button("💬 Conversation Starters"):
        st.session_state.quick_prompt = (
            "Suggest conversation starters for the next coaching session."
        )

with col4:
    if st.button("📈 Progress Summary"):
        st.session_state.quick_prompt = (
            "Summarize recent student progress and setbacks."
        )

st.divider()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Ask about a student, signal, concern, or coaching strategy...")

if st.session_state.get("quick_prompt"):
    prompt = st.session_state.quick_prompt
    st.session_state.quick_prompt = None

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("assistant"):
        with st.spinner("Analyzing student context..."):
            try:
                response = coachChatResponse(prompt)

                st.markdown(response)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": response,
                    }
                )

            except Exception as e:
                error_msg = f"Error generating response: {str(e)}"

                st.error(error_msg)
                st.code(traceback.format_exc())
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_msg,
                    }
                )

with st.sidebar:
    st.header("Coach Tools")

    if st.button("🧹 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    st.markdown(f"**Messages:** {len(st.session_state.messages)}")

    st.caption(
        "Coach Copilot can access student memories, session summaries, and coaching signals through connected tools."
    )
