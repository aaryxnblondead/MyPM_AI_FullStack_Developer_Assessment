import time

from fastapi import HTTPException

from app.config import settings


def doc_prompt(text: str) -> str:
    return f"title: none | text: {text}"


def query_prompt(text: str) -> str:
    return f"task: search result | query: {text}"


def _embed_batch(texts: list[str]) -> list[list[float]]:
    from google import genai
    from google.genai import types

    if not settings.gemini_api_key:
        raise HTTPException(status_code=502, detail="Embeddings are not configured. Set GEMINI_API_KEY.")
    client = genai.Client(api_key=settings.gemini_api_key)
    out: list[list[float]] = []
    for t in texts:
        last: Exception | None = None
        for attempt in range(3):
            try:
                res = client.models.embed_content(
                    model=settings.embedding_model,
                    contents=t,
                    config=types.EmbedContentConfig(output_dimensionality=settings.embedding_dim),
                )
                vals = list(res.embeddings[0].values)
                if len(vals) != settings.embedding_dim:
                    raise ValueError(f"expected dim {settings.embedding_dim}, got {len(vals)}")
                out.append(vals)
                last = None
                break
            except Exception as e:
                last = e
                time.sleep(0.5 * (attempt + 1))
        if last is not None:
            raise HTTPException(status_code=502, detail="Embedding request failed. Try again.") from last
    return out


def embed_documents(texts: list[str]) -> list[list[float]]:
    return _embed_batch([doc_prompt(t) for t in texts])


def embed_query(text: str) -> list[float]:
    return _embed_batch([query_prompt(text)])[0]
