from app.services import skills_db


def test_known_skills_loaded():
    known = skills_db.load_known_skills()
    assert len(known) > 10000
    assert skills_db.is_known("HubSpot")
    assert skills_db.is_known("customer retention")
    assert not skills_db.is_known("Salesforce XYZ Not A Skill 12345")


def test_junk_filtered():
    assert not skills_db.is_known("1.0")
    assert not skills_db.is_known("2.0.1")


def test_find_in_text_grounded():
    text = "Riya Shah has five years of B2B SaaS customer success experience. Used HubSpot."
    hits = skills_db.find_in_text(text)
    names = {h["name"] for h in hits}
    assert "hubspot" in names
    assert "saas" in names
    for h in hits:
        assert h["source"].lower() in text.lower()
    assert "salesforce" not in names


def test_stemming_matches_variants():
    assert skills_db.stem_word("accounts") == skills_db.stem_word("account")
    assert skills_db.stem_word("managed") == skills_db.stem_word("manage")
    hits = skills_db.find_in_text("Managed 25 client account work.")
    names = {h["name"] for h in hits}
    assert "client accounts" in names


def test_novel_section_skill_treated_as_skill():
    text = "Experience:\nDid support work.\nSkills:\nZorblax Framing, HubSpot"
    items = skills_db.extract_skills_section(text)
    names = {i["name"].lower() for i in items}
    assert "zorblax framing" in names
    assert "hubspot" in names
    for i in items:
        assert i["source"] in text
