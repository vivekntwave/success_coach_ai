from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
import streamlit as st
from app.prompts import COACH_COPILOT_SYSTEM_PROMPT
from app.services.google_sheet_service import get_all_sheet_data
from chroma_db.chroma_client import search_knowledge_base

load_dotenv()


model = init_chat_model(model="gpt-5.4-mini-2026-03-17", temperature=0.5, timeout=300)


def coachChatResponse(user_prompt: str):
    agent = create_agent(
        model=model,
        tools=[search_knowledge_base, get_all_sheet_data],
        system_prompt=COACH_COPILOT_SYSTEM_PROMPT,
    )
    result = agent.invoke(
        {
            "messages": st.session_state.messages[-30:]
            + [{"role": "user", "content": user_prompt}]
        }
    )
    return result["messages"][-1].content_blocks[0]["text"]
