from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from chroma_db.chroma_client import search_knowledge_base
from services.google_sheet_service import googleSheetData
import streamlit as st

load_dotenv()
STUDENT_ID = "STU001"

SYSTEM_PROMPT = f"""
You are Success Coach AI, an evidence-based coach focused on helping users achieve goals through practical, measurable actions. 
Only use information explicitly provided by the user or available in verified context; never invent facts, progress, or outcomes. 
Give actionable recommendations with clear reasoning, benefits, risks, and tradeoffs, and distinguish facts from assumptions. 
If critical information is missing, ask focused questions instead of guessing. 
Be supportive but realistic, prioritize accuracy over motivation, and never guarantee success or future results.
The user data is as follows:{googleSheetData(STUDENT_ID)}"""

model = init_chat_model(model="gpt-5.4-mini-2026-03-17", temperature=0.5, timeout=300)


def chatResponse(user_prompt: str):
    agent = create_agent(
        model=model, tools=[search_knowledge_base], system_prompt=SYSTEM_PROMPT
    )
    result = agent.invoke(
        {
            "messages": st.session_state.messages[-30:]
            + [{"role": "user", "content": user_prompt}]
        }
    )
    return result["messages"][-1].content_blocks[0]["text"]
