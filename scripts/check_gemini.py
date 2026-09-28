"""Smoke test Gemini embedding plus schema constrained generation."""
import json
import os
import sys

from dotenv import load_dotenv

load_dotenv(".env")
load_dotenv("backend/.env")


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def main() -> None:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        fail("GEMINI_API_KEY is empty. Set it in .env. See .env.example.")
    llm_model = os.getenv("LLM_MODEL", "gemini-2.5-flash")
    emb_model = os.getenv("EMBEDDING_MODEL", "gemini-embedding-2")
    try:
        from google import genai
        from google.genai import types
    except Exception as e:
        fail(f"could not import google-genai: {e}")

    client = genai.Client(api_key=key)

    try:
        emb = client.models.embed_content(
            model=emb_model,
            contents="task: search result | query: customer retention",
            config=types.EmbedContentConfig(output_dimensionality=768),
        )
    except Exception as e:
        fail(f"embedding call failed for {emb_model}: {e}")

    values = []
    try:
        first = emb.embeddings[0]
        values = list(first.values)
    except Exception as e:
        fail(f"could not read embedding values: {e} raw={emb}")
    print(f"embedding_model={emb_model} dim={len(values)}")

    schema = {
        "type": "object",
        "properties": {"status": {"type": "string"}},
        "required": ["status"],
    }
    try:
        res = client.models.generate_content(
            model=llm_model,
            contents="Reply with status ok.",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
            ),
        )
    except Exception as e:
        fail(f"generation call failed for {llm_model}: {e}")

    try:
        parsed = json.loads(res.text or "")
    except Exception as e:
        fail(f"model did not return valid JSON: {e} text={res.text!r}")
    if parsed.get("status") != "ok":
        fail(f"unexpected JSON {parsed}")
    print(f"llm_model={llm_model} json={parsed} ok")


if __name__ == "__main__":
    main()
