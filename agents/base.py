"""Base agent class — thin wrapper around Gemini for all agents."""
import json
import asyncio
import re
from typing import Optional
from google import genai
from google.genai import types
from google.genai import errors as genai_errors
from config import GEMINI_API_KEY


# Single shared client (reused across all agents)
_client = genai.Client(api_key=GEMINI_API_KEY)

# How many times to retry a transient error before giving up
_MAX_RETRIES = 4

# Status codes worth retrying: 429 rate limit, 500/503 transient server errors
_RETRYABLE_CODES = {429, 500, 503}


def _retry_delay_seconds(err, attempt: int) -> float:
    """Wait time before the next retry.

    Honors the 'retry in Ns' hint when present (429s), otherwise backs off
    exponentially (2s, 4s, 8s, ...) for transient 5xx errors.
    """
    match = re.search(r"retry in ([\d.]+)s", str(err), re.IGNORECASE)
    if match:
        return min(float(match.group(1)) + 1.0, 30.0)
    return min(2.0 * (2 ** attempt), 30.0)


class Agent:
    def __init__(
        self,
        name: str,
        model: str,
        system_prompt: str,
        temperature: float = 0.3,
    ):
        self.name = name
        self.model = model
        self.system_prompt = system_prompt
        self.temperature = temperature

    async def run(self, user_input: str, expect_json: bool = False) -> str | dict | list:
        """Send user_input to Gemini, return text or parsed JSON."""
        config = types.GenerateContentConfig(
            system_instruction=self.system_prompt,
            temperature=self.temperature,
            response_mime_type="application/json" if expect_json else "text/plain",
        )

        # genai SDK is sync; offload to thread so we don't block the event loop.
        # Retry transient errors (429 rate spikes, 500/503 server overload) with
        # backoff. A truly exhausted daily quota will surface once retries run out.
        resp = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                resp = await asyncio.to_thread(
                    _client.models.generate_content,
                    model=self.model,
                    contents=user_input,
                    config=config,
                )
                break
            except genai_errors.APIError as e:
                if e.code in _RETRYABLE_CODES and attempt < _MAX_RETRIES:
                    await asyncio.sleep(_retry_delay_seconds(e, attempt))
                    continue
                raise

        text = resp.text or ""

        if expect_json:
            try:
                return json.loads(text)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"[{self.name}] expected JSON, got:\n{text[:500]}\nError: {e}"
                )
        return text

    def __repr__(self) -> str:
        return f"<Agent name={self.name} model={self.model}>"