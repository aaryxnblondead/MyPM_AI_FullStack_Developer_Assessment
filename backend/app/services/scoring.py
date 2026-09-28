from app.config import settings

VALUES = {"met": 1.0, "partial": 0.5, "no_evidence": 0.0}

NO_EVIDENCE_TEXT = "No evidence found in resume"


def score_requirements(requirements: list[dict], verdicts: list[dict]) -> dict:
    by_id = {v["requirement_id"]: v for v in verdicts}
    total_w = 0.0
    earned = 0.0
    must_total = 0
    must_miss = 0
    for r in requirements:
        w = settings.must_have_weight if r.get("must_have") else settings.nice_to_have_weight
        total_w += w
        v = by_id.get(r["id"], {}).get("verdict", "no_evidence")
        earned += VALUES.get(v, 0.0) * w
        if r.get("must_have"):
            must_total += 1
            if v == "no_evidence":
                must_miss += 1
    score = round(100.0 * earned / total_w, 1) if total_w else 0.0
    if score >= settings.strong_fit_min:
        category = "Strong Fit"
    elif score >= settings.moderate_fit_min:
        category = "Moderate Fit"
    else:
        category = "Weak Fit"
    if must_total and (must_miss / must_total) > settings.must_have_miss_cap_share:
        if category == "Strong Fit":
            category = "Moderate Fit"
    return {
        "fit_score": score,
        "fit_category": category,
        "must_miss": must_miss,
        "must_total": must_total,
    }
