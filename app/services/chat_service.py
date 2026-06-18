from dotenv import load_dotenv
from mem0 import MemoryClient
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
import os

load_dotenv()
MEM0_API_KEY = os.getenv("MEM0_API_KEY")


SYSTEM_PROMPT = """You are a literary data assistant.

## Capabilities

- `fetch_text_from_url`: loads document text from a URL into the conversation.
Do not guess line counts or positions—ground them in tool results from the saved file."""

model = init_chat_model(model="gpt-5.4-mini-2026-03-17", temperature=0.5, timeout=300)


client = MemoryClient(api_key=MEM0_API_KEY)


def chatResponse(user_prompt: str):
    agent = create_agent(model=model, system_prompt=SYSTEM_PROMPT)
    result = agent.invoke({"messages": [{"role": "user", "content": user_prompt}]})
    return result["messages"][-1].content_blocks[0]["text"]
