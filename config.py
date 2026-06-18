import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

MODEL_PRO = "gemini-2.5-flash"
MODEL_FLASH = "gemini-2.5-flash-lite"

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY missing in .env")