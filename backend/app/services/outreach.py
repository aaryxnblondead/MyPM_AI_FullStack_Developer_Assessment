import re

from app.prompts.outreach import OUTREACH_SCHEMA, OUTREACH_SYSTEM, outreach_user
from app.services.llm import generate_json


def _words(s: str) -> set[str]:
    return set(re.findall(r"[a-z]{3,}", s.lower()))


def normalize_body(body: str) -> str:
    """Normalize line endings and paragraph spacing without flattening."""
    text = body.replace("\r\n", "\n").replace("\r", "\n")
    lines = [ln.rstrip() for ln in text.split("\n")]
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip("\n ")


def truncate_words(text: str, limit: int = 150) -> str:
    """Truncate to `limit` words while preserving original line breaks."""
    parts = re.split(r"(\s+)", text)
    words = 0
    out: list[str] = []
    for p in parts:
        if not p:
            continue
        if re.fullmatch(r"\s+", p):
            out.append(p)
            continue
        words += 1
        if words > limit:
            break
        out.append(p)
    return "".join(out).strip()


def shape_email(body: str) -> str:
    """Enforce email line breaks even if the LLM returns one flat paragraph."""
    text = normalize_body(body)
    # Greeting on its own line: "Hi Riya, <rest>" -> "Hi Riya,\n\n<rest>"
    m = re.match(r"^(Hi [^,\n]{1,40},)[ \t]+(\S.*)$", text, re.DOTALL)
    if m and "\n" not in m.group(1):
        text = m.group(1).rstrip() + "\n\n" + m.group(2).lstrip()
    # Sign-off on its own lines: "... availability. Best, {Recruiter Name}"
    text = re.sub(r"[ \t]*\n?[ \t]*Best,[ \t]*\n?[ \t]*(\{Recruiter Name\})", r"\n\nBest,\n\1", text)
    return normalize_body(text)


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
    body = normalize_body(str(out.get("body", "")))
    if not subject or not body:
        raise ValueError("empty outreach")
    if len(body.split()) > 150:
        body = normalize_body(truncate_words(body, 150))
    # Ensure email shape: greeting, blank line, paragraphs, blank line, sign-off.
    if "Best," not in body:
        body = normalize_body(body + "\n\nBest,\n{Recruiter Name}")
    body = shape_email(body)
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
