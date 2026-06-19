from dotenv import load_dotenv
from mem0 import MemoryClient
from pathlib import Path
import os

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")
MEM0_API_KEY = os.getenv("MEM0_API_KEY")
client = MemoryClient(api_key=MEM0_API_KEY)
