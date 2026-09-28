"""Nonce delimited wrapping so untrusted text stays data."""
import re
import secrets

TAG_RE = re.compile(r"</?(?:resume_chunk|requirement|resume|jd|verdicts|evidence)[^>]*>", re.IGNORECASE)


def new_nonce() -> str:
    return secrets.token_hex(8)


def clean_block(text: str, nonce: str) -> str:
    t = TAG_RE.sub("", text)
    return t.replace(nonce, "")


def wrap_chunk(chunk_id: str, text: str, nonce: str) -> str:
    safe = clean_block(text, nonce)
    return f'<resume_chunk id="{chunk_id}" nonce="{nonce}">{safe}</resume_chunk>'


def wrap_requirement(req_id: str, text: str, nonce: str) -> str:
    safe = clean_block(text, nonce)
    return f'<requirement id="{req_id}" nonce="{nonce}">{safe}</requirement>'
