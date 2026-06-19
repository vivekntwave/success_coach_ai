import streamlit as st
from dotenv import load_dotenv
from mem0 import MemoryClient
from pathlib import Path
import os
from langchain.tools import tool
from typing import Any, cast
from datetime import datetime, timedelta

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")
MEM0_API_KEY = os.getenv("MEM0_API_KEY")
mem0_client = MemoryClient(api_key=MEM0_API_KEY)
STUDENT_ID = st.session_state.student_id or "STU001"


def mem0_setup():
    mem0_client.project.update(
        custom_categories=cast(
            Any,
            [
                {
                    "student_goals": "Academic, career, personal growth, behavioral, or life goals the student wants to achieve."
                },
                {
                    "student_challenges": "Obstacles, difficulties, recurring struggles, blockers, or problems that hinder progress."
                },
                {
                    "stress_triggers": "Situations, events, thoughts, people, environments, or circumstances that consistently cause stress, anxiety, overwhelm, or self-doubt."
                },
                {
                    "motivators": "Factors that increase motivation, engagement, commitment, confidence, accountability, or persistence."
                },
                {
                    "habits_and_routines": "Recurring study habits, productivity systems, routines, behaviors, and lifestyle patterns."
                },
                {
                    "learning_preferences": "Preferred coaching styles, communication styles, learning methods, study approaches, and feedback preferences."
                },
                {
                    "strengths": "Skills, talents, positive traits, capabilities, and resources that support the student's success."
                },
                {
                    "growth_areas": "Skills, mindsets, habits, competencies, or behaviors that need improvement or development."
                },
                {
                    "success_patterns": "Strategies, interventions, routines, environments, or actions that have repeatedly helped the student succeed."
                },
                {
                    "failure_patterns": "Recurring behaviors, beliefs, habits, or situations that repeatedly lead to setbacks, avoidance, procrastination, or poor outcomes."
                },
                {
                    "coach_insights": "Higher-level coaching observations, inferred root causes, behavioral patterns, recurring themes, and longitudinal insights gathered across sessions."
                },
                {
                    "personal_context": "Important personal facts, background information, responsibilities, relationships, interests, and life circumstances relevant to coaching."
                },
                {
                    "session_summaries": "Summaries of completed coaching sessions including topics discussed, insights discovered, decisions made, action items, commitments, progress, and follow-up plans."
                },
            ],
        )
    )

    mem0_client.project.update(
        custom_instructions="""
        Store two distinct types of memory:

        1. Factual memories:
            - goals
            - challenges
            - stress triggers
            - habits
            - strengths
            - growth areas
            - success patterns
            - failure patterns
            - coach insights
            - personal context

        These memories should be reusable across future coaching sessions and should influence how the coach responds.

        2. Session summaries:
            - discussion topics
            - key insights
            - decisions
            - commitments
            - action plans
            - progress updates

        Session summaries should capture what happened during a specific coaching session and be useful for future briefings.

        Ignore greetings, filler conversation, acknowledgements, and casual small talk.
        """
    )


def retrieve_fresh_memories(query: str) -> str:
    yesterday = datetime.now() - timedelta(days=-1)
    fresh_memories = mem0_client.get_all(
        filters={"AND": [{"created_at": {"gte": datetime.now()}}]}
    )
    fresh_memory_context = "\n".join(
        memory["memory"] for memory in fresh_memories["results"]
    )
    return fresh_memory_context


def retrieve_profile_memories() -> str:
    profile_memories = mem0_client.search(
        query="""
        goals,
        challenges,
        stress triggers,
        habits,
        strengths,
        growth areas,
        success patterns,
        failure patterns,
        coach insights,
        personal context
        """,
        filters={"user_id": st.session_state.student_id},
        limit=30,
    )
    memory_context = "\n".join(
        memory["memory"] for memory in profile_memories["results"]
    )
    return memory_context


@tool
def retrieve_memories(query: str, limit: int = 5) -> str:
    """
    Retrieve memories from Mem0 based on a query.

    Args:
        query (str): The search query to retrieve memories.
        limit (int): The maximum number of memories to retrieve. Default is 5.
    """
    memories = mem0_client.search(query, filters={"user_id": STUDENT_ID}, top_k=limit)
    context = "\\n".join(m["memory"] for m in memories["results"])
    return context


if __name__ == "__main__":
    mem0_setup()
