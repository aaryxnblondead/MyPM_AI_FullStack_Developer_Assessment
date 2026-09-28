from app.services import chunker


def test_chunk_offsets_point_back_to_text():
    text = "Experience:\nDid support work for five years.\nEducation:\nBSc Test Uni."
    chunks = chunker.chunk_text(text)
    assert len(chunks) >= 2
    for i, c in enumerate(chunks):
        assert c["chunk_index"] == i
        assert text[c["char_start"] : c["char_end"]] == c["text"]
        assert c["char_start"] < c["char_end"]
    labels = {c["section_label"] for c in chunks}
    assert "experience" in labels or "education" in labels


def test_long_section_splits_with_overlap():
    text = "Experience:\n" + ("Handled accounts and renewals. " * 120)
    chunks = chunker.chunk_text(text)
    assert len(chunks) >= 2
    for c in chunks:
        assert len(c["text"]) <= 1200
        assert c["section_label"] == "experience"
