from dotenv import load_dotenv
from mem0 import MemoryClient
from pathlib import Path
import os
import streamlit as st
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
import json

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")
MEM0_API_KEY = os.getenv("MEM0_API_KEY")
mem0_client = MemoryClient(api_key=MEM0_API_KEY)
STUDENT_ID = st.session_state.student_id or "STU001"

FACTUAL_EXTRACTION_PROMPT = """
You are a memory-extraction assistant for a student coaching platform.
 
Given a list of things a student said during a coaching session, extract
discrete factual memories about the student.
 
Cover any of: goals, challenges, stress triggers, motivators,
habits_and_routines, learning_preferences, strengths, growth_areas,
success_patterns, failure_patterns, coach_insights, personal_context.
 
Rules:
- One fact per item — short, specific, reusable across future sessions.
- Skip greetings, filler, acknowledgements, and casual small talk.
- If nothing factual is present, return an empty array.
 
Return ONLY valid JSON — no markdown fences, no preamble:
{"factual_memories": ["...", "..."]}
"""

SESSION_SUMMARY_PROMPT = """
You are a coaching session summariser.
 
Given a full coaching conversation (both coach and student turns), write a
single summary paragraph of 4–6 sentences covering:
- The main topics discussed
- Key insights or realisations the student had
- Decisions made and commitments or action items agreed on
- Any follow-up plans
 
Return ONLY valid JSON — no markdown fences, no preamble:
{"session_summary": "..."}
"""
model = init_chat_model(model="gpt-5.4-mini-2026-03-17", temperature=0.5, timeout=300)


def call_llm(prompt: str, user_content: str):
    agent = create_agent(model=model, system_prompt=prompt)
    results = agent.invoke({"messages": [{"role": "user", "content": user_content}]})
    response_text = results["messages"][-1].content_blocks[0]["text"]
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        return {"factual_memories": []}


def auto_save_factual_memories() -> int:
    messages: list[dict] = st.session_state.get("messages", [])
    last_index: int = st.session_state.last_saved_index

    new_messages = messages[last_index:]
    new_student_messages = [m["content"] for m in new_messages if m["role"] == "user"]

    if not new_student_messages:
        return 0
    user_content = "\n".join(f"-{msg}" for msg in new_student_messages)
    extracted = call_llm(FACTUAL_EXTRACTION_PROMPT, user_content)
    factual_memories: list[str] = extracted.get("factual_memories", [])
    for memory in factual_memories:
        mem0_client.add(
            messages=[{"role": "user", "content": memory}],
            user_id=STUDENT_ID,
        )

    st.session_state.last_saved_index = len(messages)

    return len(factual_memories)


def session_summary():
    if st.session_state.session_summary_saved:
        return ""

    auto_save_factual_memories()

    messages: list[dict] = st.session_state.get("messages", [])
    if not messages:
        return ""

    conversation = "\n".join(
        f"{m['role'].capitalize()}: {m['content']}" for m in messages
    )

    extracted = call_llm(SESSION_SUMMARY_PROMPT, conversation)
    summary = extracted.get("session_summary", "")

    if summary:
        content = (
            f"{st.session_state.session_id}: {summary}"
            if st.session_state.session_id
            else summary
        )
        mem0_client.add(
            messages=[{"role": "assistant", "content": content}],
            user_id=STUDENT_ID,
            metadata={"category": "session_summaries"},
        )
        st.session_state.session_summary_saved = True

    return summary
