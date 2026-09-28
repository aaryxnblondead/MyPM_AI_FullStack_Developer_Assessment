import re

SECTION_PATTERNS = [
    (re.compile(r"^\s*(work\s+)?experience\s*:?\s*$", re.I), "experience"),
    (re.compile(r"^\s*education\s*:?\s*$", re.I), "education"),
    (re.compile(r"^\s*skills?\s*:?\s*$", re.I), "skills"),
    (re.compile(r"^\s*projects?\s*:?\s*$", re.I), "projects"),
    (re.compile(r"^\s*summary\s*:?\s*$", re.I), "summary"),
]

TARGET = 1200
OVERLAP = 150


def split_sections(text: str) -> list[tuple[str, int, int]]:
    lines = text.splitlines(keepends=True)
    sections: list[tuple[str, int, int]] = []
    current = "general"
    start = 0
    pos = 0
    for line in lines:
        stripped = line.strip()
        hit = None
        for pat, label in SECTION_PATTERNS:
            if pat.match(stripped):
                hit = label
                break
        if hit:
            if pos > start:
                sections.append((current, start, pos))
            current = hit
            start = pos
        pos += len(line)
    if pos > start:
        sections.append((current, start, pos))
    if not sections:
        sections.append(("general", 0, len(text)))
    return sections


def chunk_text(text: str) -> list[dict]:
    sections = split_sections(text)
    chunks: list[dict] = []
    for label, s, e in sections:
        i = s
        while i < e:
            j = min(i + TARGET, e)
            chunk = text[i:j]
            chunks.append(
                {
                    "section_label": label,
                    "text": chunk,
                    "char_start": i,
                    "char_end": j,
                }
            )
            if j >= e:
                break
            i = max(j - OVERLAP, i + 1)
    for idx, c in enumerate(chunks):
        c["chunk_index"] = idx
    return chunks
