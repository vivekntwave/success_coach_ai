import uuid

DEFAULTS = {
    "messages": [],
    "role": None,
    "student_id": None,
    "student_name": None,
    "last_saved_index": 0,
    "session_id": str(uuid.uuid4()),
    "session_summary_saved": False,
}

SESSION_DEFAULTS = {
    "messages": [],
    "last_saved_index": 0,
    "session_id": str(uuid.uuid4()),
    "session_summary_saved": False,
}
