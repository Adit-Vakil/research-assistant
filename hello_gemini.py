from google import genai
from config import GEMINI_API_KEY, MODEL_FLASH

client = genai.Client(api_key=GEMINI_API_KEY)

resp = client.models.generate_content(
    model=MODEL_FLASH,
    contents="Reply with exactly: PONG",
)

print(resp.text)