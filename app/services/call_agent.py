import json
from app.prompts import ACCUMULATE_SIGNAL_PROMPT
from app.services.mem0_upload_service import call_llm


def merge_signals_with_llm(existing_signal, new_signal):

    user_content = f"""
Existing unresolved signal:

{json.dumps(existing_signal, indent=2)}

New signal:

{json.dumps(new_signal, indent=2)}
"""

    return call_llm(ACCUMULATE_SIGNAL_PROMPT, user_content)
