"""Extract design tokens from design/css with file:line refs."""
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS_DIR = ROOT / "design" / "css"
OUT_JSON = ROOT / "design" / "design-tokens.json"

HEX_RE = re.compile(r"#([0-9a-fA-F]{3,8})\b")
PROP_RE = re.compile(r"--([\w-]+)\s*:\s*([^;]+);")
FONT_FAMILY_RE = re.compile(r"font-family\s*:\s*([^;]+);")
SIZE_RE = re.compile(r"font-size\s*:\s*([^;]+);")
RADIUS_RE = re.compile(r"border-radius\s*:\s*([^;]+);")
SHADOW_RE = re.compile(r"box-shadow\s*:\s*([^;]+);")
TRANS_RE = re.compile(r"transition\s*:\s*([^;]+);")
Z_RE = re.compile(r"z-index\s*:\s*([^;]+);")
MEDIA_RE = re.compile(r"@media\s*([^{]+)\{")
BTN_RE = re.compile(r"([^{}]*\.(?:theme-btn|btn|cta)[^{}]*)\{")


def norm_hex(h: str) -> str:
    h = h.lower()
    if len(h) == 4:
        return "#" + "".join(c * 2 for c in h[1:])
    return h


def main() -> None:
    files = sorted(CSS_DIR.glob("*.css"))
    colors: Counter = Counter()
    color_refs: dict[str, list[str]] = {}
    props: dict[str, dict] = {}
    fonts: Counter = Counter()
    sizes: Counter = Counter()
    radii: Counter = Counter()
    shadows: Counter = Counter()
    transitions: Counter = Counter()
    zindexes: Counter = Counter()
    breakpoints: Counter = Counter()
    buttons: list[dict] = []

    for path in files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for i, line in enumerate(text.splitlines(), 1):
            ref = f"{path.name}:{i}"
            for m in HEX_RE.finditer(line):
                hx = norm_hex("#" + m.group(1))
                if len(hx) not in (7, 9):
                    continue
                colors[hx] += 1
                color_refs.setdefault(hx, []).append(ref)
            for m in PROP_RE.finditer(line):
                props[f"--{m.group(1)}"] = {"value": m.group(2).strip(), "ref": ref}
            for m in FONT_FAMILY_RE.finditer(line):
                fonts[m.group(1).strip()[:120]] += 1
            for m in SIZE_RE.finditer(line):
                sizes[m.group(1).strip()[:40]] += 1
            for m in RADIUS_RE.finditer(line):
                radii[m.group(1).strip()[:40]] += 1
            for m in SHADOW_RE.finditer(line):
                shadows[m.group(1).strip()[:120]] += 1
            for m in TRANS_RE.finditer(line):
                transitions[m.group(1).strip()[:120]] += 1
            for m in Z_RE.finditer(line):
                zindexes[m.group(1).strip()[:20]] += 1
            for m in MEDIA_RE.finditer(line):
                breakpoints[m.group(1).strip()[:80]] += 1

    style_text = (CSS_DIR / "style.css").read_text(encoding="utf-8", errors="ignore")
    for m in BTN_RE.finditer(style_text):
        sel = " ".join(m.group(1).split())[:160]
        buttons.append({"selector": sel})

    data = {
        "meta": {"files": len(files), "source": "design/css/*.css"},
        "custom_properties": props,
        "colors_by_frequency": [
            {"hex": hx, "count": c, "refs": color_refs[hx][:6]} for hx, c in colors.most_common(40)
        ],
        "font_families": [{"stack": k, "count": v} for k, v in fonts.most_common(20)],
        "font_sizes": [{"value": k, "count": v} for k, v in sizes.most_common(20)],
        "radii": [{"value": k, "count": v} for k, v in radii.most_common(20)],
        "shadows": [{"value": k, "count": v} for k, v in shadows.most_common(10)],
        "transitions": [{"value": k, "count": v} for k, v in transitions.most_common(10)],
        "z_index": [{"value": k, "count": v} for k, v in zindexes.most_common(10)],
        "breakpoints": [{"query": k, "count": v} for k, v in breakpoints.most_common(20)],
        "button_selectors": buttons[:30],
    }
    OUT_JSON.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"wrote {OUT_JSON} from {len(files)} files")


if __name__ == "__main__":
    main()
