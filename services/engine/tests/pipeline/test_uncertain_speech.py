from engine.pipeline.align import IdMinter, align
from engine.pipeline.announce import announcements
from tests.factories import candidate_code, candidate_sheet


def test_unclear_old_value_is_not_repeated_as_fact_when_it_becomes_clear() -> None:
    minter = IdMinter()
    old = candidate_sheet(["Name", "Revenue"], [["Acme", "999"]])
    assert old.sheet is not None
    old.sheet.rows[0].cells[1].uncertain = True
    old = align(None, old, minter).doc
    result = align(old, candidate_sheet(["Name", "Revenue"], [["Acme", "100"]]), minter)
    speech = announcements(result.changes, result.doc.version, "old_to_new", None)
    assert speech[0].text == "Acme, Revenue: unclear to 100."
    assert "999" not in speech[0].text


def test_added_uncertain_code_line_never_speaks_the_guessed_text() -> None:
    minter = IdMinter()
    old = align(None, candidate_code(["x = 1"]), minter).doc
    new = candidate_code(["x = 1", "secret_guess = 999"])
    assert new.code is not None
    new.code.lines[1].uncertain = True
    result = align(old, new, minter)
    texts = [a.text for a in announcements(result.changes, result.doc.version, "old_to_new", None)]
    assert any("unclear" in t for t in texts)
    assert all("secret_guess" not in t and "999" not in t for t in texts)


def test_uncertainty_change_without_a_text_change_is_announced() -> None:
    minter = IdMinter()
    old = align(None, candidate_sheet(["Name", "Revenue"], [["Acme", "100"]]), minter).doc
    new = candidate_sheet(["Name", "Revenue"], [["Acme", "100"]])
    assert new.sheet is not None
    new.sheet.rows[0].cells[1].uncertain = True
    result = align(old, new, minter)
    [spoken] = announcements(result.changes, result.doc.version, "old_to_new", None)
    assert spoken.kind == "uncertain" and "100" not in spoken.text
