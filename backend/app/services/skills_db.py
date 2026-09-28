"""Known skills reference for recall support. Matches only text that is present."""
import re
from functools import lru_cache
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "all_skills.txt"

VERSION_RE = re.compile(r"^[0-9vV\.\-\+xX/\(\) ]+$")
WORD_RE = re.compile(r"[A-Za-z]+")


def normalize(name: str) -> str:
    return name.strip().strip("'\"").strip().lower()


def is_junk(normalized: str) -> bool:
    if len(normalized) < 2:
        return True
    if VERSION_RE.match(normalized):
        return True
    return False


def stem_word(word: str) -> str:
    w = word.lower()
    if len(w) <= 3:
        return w
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"
    if w.endswith(("sses", "xes", "zes", "ches", "shes")) and len(w) > 5:
        return w[:-2]
    if w.endswith("s") and not w.endswith("ss") and len(w) > 3:
        w = w[:-1]
    if w.endswith("ing") and len(w) > 6:
        w = w[:-3]
    elif w.endswith("ed") and len(w) > 5:
        w = w[:-2]
    if w.endswith("e") and len(w) > 4 and w[-2] not in "aeiou":
        w = w[:-1]
    return w


def stem_phrase(phrase: str) -> str:
    return " ".join(stem_word(w) for w in WORD_RE.findall(phrase.lower()))


@lru_cache(maxsize=1)
def load_known_skills() -> set[str]:
    out: set[str] = set()
    if not DATA_PATH.exists():
        return out
    for line in DATA_PATH.read_text(encoding="utf-8", errors="ignore").splitlines():
        n = normalize(line)
        if not n or is_junk(n):
            continue
        out.add(n)
    return out


def is_known(name: str) -> bool:
    return normalize(name) in load_known_skills()


def _exact_hits(text: str, lowered: str, limit: int) -> list[tuple[str, str, int, int]]:
    known = load_known_skills()
    hits: list[tuple[str, str, int, int]] = []
    candidates = sorted((k for k in known if len(k) >= 2), key=len, reverse=True)
    seen: set[str] = set()
    for skill in candidates:
        if skill in seen:
            continue
        if skill not in lowered:
            continue
        pat = r"(?<![A-Za-z0-9+#.])" + re.escape(skill) + r"(?![A-Za-z0-9+#.])"
        m = re.search(pat, lowered)
        if not m:
            continue
        seen.add(skill)
        start, end = m.start(), m.end()
        hits.append((skill, text[start:end], start, end))
        if len(hits) >= limit:
            break
    return hits


def _stemmed_hits(text: str, limit: int, skip: set[str]) -> list[tuple[str, str, int, int]]:
    known = load_known_skills()
    tokens = [(m.group(0), m.start(), m.end()) for m in WORD_RE.finditer(text)]
    if not tokens:
        return []
    stems = [stem_word(w) for w, _, _ in tokens]
    index: dict[str, list[tuple[str, list[str]]]] = {}
    for skill in known:
        if len(skill) < 2 or skill in skip:
            continue
        if re.search(r"[^a-z\s\-]", skill):
            continue
        parts = [stem_word(w) for w in WORD_RE.findall(skill)]
        if not parts:
            continue
        index.setdefault(parts[0], []).append((skill, parts))
    hits: list[tuple[str, str, int, int]] = []
    seen: set[str] = set()
    for i in range(len(tokens)):
        for skill, parts in index.get(stems[i], []):
            if skill in seen:
                continue
            if stems[i : i + len(parts)] != parts:
                continue
            seen.add(skill)
            _, s, _ = tokens[i]
            _, _, e = tokens[i + len(parts) - 1]
            hits.append((skill, text[s:e], s, e))
            if len(hits) >= limit:
                return hits
    return hits


def _dedupe_spans(hits: list[tuple[str, str, int, int]]) -> list[tuple[str, str, int, int]]:
    ordered = sorted(hits, key=lambda h: (h[3] - h[2], len(h[0])), reverse=True)
    kept: list[tuple[str, str, int, int]] = []
    for h in ordered:
        if any(not (h[3] <= k[2] or h[2] >= k[3]) for k in kept):
            continue
        kept.append(h)
    return kept


def find_in_text(text: str, limit: int = 40) -> list[dict[str, str]]:
    if not text.strip() or not load_known_skills():
        return []
    lowered = text.lower()
    exact = _exact_hits(text, lowered, limit)
    skip = {h[0] for h in exact}
    rest = max(0, limit - len(exact))
    stemmed = _stemmed_hits(text, rest, skip) if rest else []
    merged = _dedupe_spans(exact + stemmed)
    merged.sort(key=lambda h: len(h[0]), reverse=True)
    return [{"name": n, "source": s} for n, s, _, _ in merged[:limit]]


def extract_skills_section(text: str) -> list[dict[str, str]]:
    from app.services import chunker

    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for label, s, e in chunker.split_sections(text):
        if label != "skills":
            continue
        section = text[s:e]
        parts = re.split(r"[\n,;|•·▪●\-*]+", section)
        for raw in parts:
            name = raw.strip().strip("'\"").strip(" :")
            if len(name) < 2 or VERSION_RE.match(name.lower()):
                continue
            if name.lower().startswith("skill"):
                continue
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            idx = section.find(raw.strip())
            if idx >= 0:
                start = s + idx + (len(raw) - len(raw.lstrip()))
                end = start + len(name)
                out.append({"name": name, "source": text[start:end]})
            else:
                out.append({"name": name, "source": name})
    return out
