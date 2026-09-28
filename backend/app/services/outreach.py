import re

from app.prompts.outreach import OUTREACH_SCHEMA, OUTREACH_SYSTEM, outreach_user
from app.services.llm import generate_json


def _words(s: str) -> set[str]:
    return set(re.findall(r"[a-z]{3,}", s.lower()))


def build_outreach(candidate_name: str, company: str, job_title: str, results: list[dict]) -> dict[str, str]:
    good = [r for r in results if r.get("verdict") in ("met", "partial") and r.get("evidence")]
    lines = []
    for r in good[:3]:
        q = r["evidence"][0]["quote"] if r["evidence"] else ""
        lines.append(f"- {r['requirement_id']}: {q}")
    evidence_block = "\n".join(lines) if lines else "No verified strengths."
    out = generate_json(
        OUTREACH_SYSTEM,
        outreach_user(candidate_name, company, job_title, evidence_block),
        OUTREACH_SCHEMA,
    )
    subject = str(out.get("subject", "")).strip()
    body = str(out.get("body", "")).strip()
    if not subject or not body:
        raise ValueError("empty outreach")
    words = len(body.split())
    if words > 150:
        body = " ".join(body.split()[:150])
    return {"subject": subject, "body": body}


def post_check_email(body: str, requirements: list[dict], results: list[dict]) -> list[str]:
    by_id = {r["requirement_id"]: r for r in results}
    bad_terms: set[str] = set()
    for req in requirements:
        v = by_id.get(req["id"], {}).get("verdict", "no_evidence")
        if v == "no_evidence":
            bad_terms |= _words(str(req.get("text", "")))
    good_terms: set[str] = set()
    for r in results:
        if r.get("verdict") in ("met", "partial"):
            for e in r.get("evidence", []):
                good_terms |= _words(str(e.get("quote", "")))
    flags: list[str] = []
    body_words = _words(body)
    for term in sorted(bad_terms - good_terms):
        if term in body_words:
            flags.append(term)
    return flags[:10]
