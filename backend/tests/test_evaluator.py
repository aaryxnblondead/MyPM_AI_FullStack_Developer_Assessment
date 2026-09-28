from types import SimpleNamespace

from app.services import evaluator


def chunk(cid: str, text: str) -> SimpleNamespace:
    return SimpleNamespace(id=cid, text=text)


def test_invalid_chunk_id_discarded():
    retrieved = {"c1": chunk("c1", "Used HubSpot daily.")}
    raw = {
        "requirement_id": "r1",
        "verdict": "met",
        "evidence": [{"chunk_id": "nope", "quote": "Used HubSpot daily."}],
        "reasoning": "x",
    }
    out = evaluator.verify_item(raw, retrieved)
    assert out["verdict"] == "no_evidence"
    assert out["evidence"] == []


def test_quote_not_in_chunk_discarded_and_downgraded():
    retrieved = {"c1": chunk("c1", "Used HubSpot daily.")}
    raw = {
        "requirement_id": "r1",
        "verdict": "met",
        "evidence": [{"chunk_id": "c1", "quote": "Knows Salesforce well."}],
        "reasoning": "x",
    }
    out = evaluator.verify_item(raw, retrieved)
    assert out["verdict"] == "no_evidence"


def test_quote_normalization_allows_case_space():
    retrieved = {"c1": chunk("c1", "  Used   HUBSPOT daily. ")}
    raw = {
        "requirement_id": "r1",
        "verdict": "partial",
        "evidence": [{"chunk_id": "c1", "quote": "used hubspot daily."}],
        "reasoning": "x",
    }
    out = evaluator.verify_item(raw, retrieved)
    assert out["verdict"] == "partial"
    assert len(out["evidence"]) == 1


def test_no_evidence_display_text():
    retrieved = {"c1": chunk("c1", "Unrelated text.")}
    raw = {"requirement_id": "r1", "verdict": "no_evidence", "evidence": [], "reasoning": "x"}
    out = evaluator.verify_item(raw, retrieved)
    assert out["verdict"] == "no_evidence"
    assert out["evidence"] == []
