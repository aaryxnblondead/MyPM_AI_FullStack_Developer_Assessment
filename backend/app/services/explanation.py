from app.prompts.explain import EXPLAIN_SCHEMA, EXPLAIN_SYSTEM, explain_user
from app.services.llm import generate_json


def build_explanation(results: list[dict]) -> str:
    lines = []
    for r in results:
        ev = "; ".join(e["quote"] for e in r.get("evidence", [])[:2]) or "No evidence found in resume"
        lines.append(f"- {r['requirement_id']}: {r['verdict']}. {ev}")
    out = generate_json(EXPLAIN_SYSTEM, explain_user("\n".join(lines)), EXPLAIN_SCHEMA)
    text = str(out.get("explanation", "")).strip()
    if not text:
        raise ValueError("empty explanation")
    return text
