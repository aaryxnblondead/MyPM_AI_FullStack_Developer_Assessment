import json
import time

from fastapi import HTTPException

from app.config import settings


def require_key() -> str:
    if not settings.gemini_api_key:
        raise HTTPException(status_code=502, detail="LLM is not configured. Set GEMINI_API_KEY.")
    return settings.gemini_api_key


def _is_rate_limit(e: Exception) -> bool:
    msg = str(e).lower()
    return "429" in msg or "resource_exhausted" in msg or "rate" in msg or "quota" in msg


def _is_timeout(e: Exception) -> bool:
    msg = str(e).lower()
    return "timeout" in msg or "deadline" in msg or "timed out" in msg


def generate_json(system: str, user: str, schema: dict, temperature: float = 0.1) -> dict:
    from google import genai
    from google.genai import types

    key = require_key()
    client = genai.Client(api_key=key)
    last: Exception | None = None
    backoff = (5.0, 20.0, 45.0)
    for attempt in range(3):
        try:
            res = client.models.generate_content(
                model=settings.llm_model,
                contents=user,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=temperature,
                ),
            )
            return json.loads(res.text or "")
        except Exception as e:
            last = e
            if _is_rate_limit(e) or _is_timeout(e):
                time.sleep(backoff[attempt])
                continue
            raise HTTPException(status_code=502, detail="LLM request failed. Try again.") from e
    assert last is not None
    if _is_timeout(last):
        raise HTTPException(status_code=504, detail="LLM timed out. Try again.") from last
    raise HTTPException(status_code=502, detail="LLM is busy. Try again.") from last
