from app.services import scoring


def reqs():
    return [
        {"id": "r1", "text": "Five years experience", "must_have": True},
        {"id": "r2", "text": "Salesforce", "must_have": True},
        {"id": "r3", "text": "Nice dashboard", "must_have": False},
    ]


def test_all_met_is_strong():
    verdicts = [
        {"requirement_id": "r1", "verdict": "met"},
        {"requirement_id": "r2", "verdict": "met"},
        {"requirement_id": "r3", "verdict": "met"},
    ]
    out = scoring.score_requirements(reqs(), verdicts)
    assert out["fit_score"] == 100.0
    assert out["fit_category"] == "Strong Fit"


def test_mixed_math_weights_must_have():
    verdicts = [
        {"requirement_id": "r1", "verdict": "met"},
        {"requirement_id": "r2", "verdict": "no_evidence"},
        {"requirement_id": "r3", "verdict": "met"},
    ]
    out = scoring.score_requirements(reqs(), verdicts)
    assert out["fit_score"] == 60.0
    assert out["fit_category"] == "Moderate Fit"


def test_boundaries():
    assert scoring.score_requirements(
        [{"id": "a", "text": "x", "must_have": True}],
        [{"requirement_id": "a", "verdict": "partial"}],
    )["fit_category"] == "Moderate Fit"
    assert scoring.score_requirements(
        [{"id": "a", "text": "x", "must_have": False}],
        [{"requirement_id": "a", "verdict": "no_evidence"}],
    )["fit_category"] == "Weak Fit"


def test_must_have_cap():
    reqs_many = [
        {"id": f"r{i}", "text": f"must {i}", "must_have": True} for i in range(4)
    ] + [{"id": "n1", "text": "nice", "must_have": False}]
    verdicts = [{"requirement_id": f"r{i}", "verdict": "no_evidence"} for i in range(3)]
    verdicts.append({"requirement_id": "r3", "verdict": "met"})
    verdicts.append({"requirement_id": "n1", "verdict": "met"})
    out = scoring.score_requirements(reqs_many, verdicts)
    assert out["must_miss"] == 3
    assert out["fit_category"] != "Strong Fit"
