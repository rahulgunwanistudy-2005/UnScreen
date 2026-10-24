from engine.model.document import FULL_FRAME
from engine.pipeline.build import build_document
from engine.pipeline.crosscheck import cross_check
from tests.factories import candidate_code, candidate_sheet, full_slide_read


def test_slide_disagreement_missing_block_and_unclear_second_read_are_flagged() -> None:
    primary = build_document(full_slide_read(["Revenue", "$100", "Growth"]), FULL_FRAME)
    read = full_slide_read(["Revenue", "$900"])
    read.blocks[0].legibility = "unsure"
    checked = cross_check(primary, build_document(read, FULL_FRAME))
    assert checked.compared == 3 and checked.disagreed == 3
    assert checked.doc.blocks is not None
    assert all(b.uncertain for b in checked.doc.blocks)
    assert checked.doc.blocks[1].text == "$100"


def test_matching_slide_is_clear_and_type_mismatch_flags_every_block() -> None:
    slide = build_document(full_slide_read(["Revenue", "$100"]), FULL_FRAME)
    assert cross_check(slide, slide).disagreed == 0
    checked = cross_check(slide, candidate_code(["print(100)"]))
    assert checked.disagreed == 2
    assert all(b.uncertain for b in checked.doc.blocks or [])


def test_unclear_code_cross_check_cannot_certify_primary_line() -> None:
    a = candidate_code(["x = 1", "y = 2"])
    b = candidate_code(["x = 1", "y = 2"])
    assert b.code is not None
    b.code.lines[1].uncertain = True
    result = cross_check(a, b)
    assert result.doc.code is not None
    assert not result.doc.code.lines[0].uncertain
    assert result.doc.code.lines[1].uncertain
    assert result.disagreed == 1


def test_missing_sheet_row_column_and_type_mismatch_are_unclear() -> None:
    a = candidate_sheet(["Name", "Value"], [["Acme", "100"], ["Beta", "200"]])
    b = candidate_sheet(["Name"], [["Acme"]])
    result = cross_check(a, b)
    assert result.doc.sheet is not None
    assert not result.doc.sheet.rows[0].cells[0].uncertain
    assert result.doc.sheet.columns[1].uncertain
    assert all(c.uncertain for c in result.doc.sheet.rows[1].cells)
    mismatch = cross_check(a, candidate_code(["x = 1"]))
    assert mismatch.disagreed == 6
    mismatch_code = cross_check(candidate_code(["x = 1"]), a)
    assert mismatch_code.disagreed == 1
