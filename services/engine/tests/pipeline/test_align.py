from engine.pipeline.align import IdMinter, align, summarize
from engine.pipeline.changes import (
    CellChanged,
    ContentTypeChanged,
    LineChanged,
    LinesChanged,
    RowsChanged,
    Scrolled,
    TitleChanged,
)
from tests.factories import candidate_code, candidate_sheet

HEADERS = ["Account", "Owner", "Q3 revenue"]
ROWS = [
    ["Acme Corp", "Asha Rao", "$1.1M"],
    ["Globex", "Ben Okafor", "$0.4M"],
    ["Initech", "Chen Wei", "$2.0M"],
    ["Hooli", "Diya Menon", "$0.9M"],
]


def first_version():
    minter = IdMinter()
    return minter, align(None, candidate_sheet(HEADERS, ROWS), minter)


def test_first_version_announces_content_type_and_mints_ids() -> None:
    _, result = first_version()
    assert result.doc.version == 1
    assert isinstance(result.changes[0], ContentTypeChanged)
    assert result.changes[0].summary == "Spreadsheet, 'Q3 Pipeline', 4 rows, 3 columns"
    sheet = result.doc.sheet
    assert sheet is not None
    assert [c.id for c in sheet.columns] == ["c1", "c2", "c3"]
    assert sheet.rows[0].cells[2].id == "r1.c3"


def test_cell_edit_keeps_ids_and_reports_old_and_new() -> None:
    minter, first = first_version()
    rows = [r[:] for r in ROWS]
    rows[0][2] = "$1.2M"
    second = align(first.doc, candidate_sheet(HEADERS, rows), minter)
    assert second.doc.sheet.rows[0].id == first.doc.sheet.rows[0].id  # type: ignore[union-attr]
    assert second.changes == [
        CellChanged("r1.c3", "r1", "c3", "Acme Corp", "Q3 revenue", "$1.1M", "$1.2M", False, False)
    ]


def test_editing_the_key_cell_still_matches_the_row() -> None:
    minter, first = first_version()
    rows = [r[:] for r in ROWS]
    rows[1][0] = "Globex Ltd"
    second = align(first.doc, candidate_sheet(HEADERS, rows), minter)
    assert [r.id for r in second.doc.sheet.rows] == [r.id for r in first.doc.sheet.rows]  # type: ignore[union-attr]
    assert len(second.changes) == 1 and isinstance(second.changes[0], CellChanged)


def test_inserted_row_gets_new_id_and_others_keep_theirs() -> None:
    minter, first = first_version()
    rows = [*ROWS[:2], ["Stark Labs", "Elif Kaya", "$3.3M"], *ROWS[2:]]
    second = align(first.doc, candidate_sheet(HEADERS, rows), minter)
    ids = [r.id for r in second.doc.sheet.rows]  # type: ignore[union-attr]
    assert ids == ["r1", "r2", "r5", "r3", "r4"]
    assert second.changes == [RowsChanged("added", ("r5",), ("Stark Labs",))]


def test_scroll_is_reported_as_scroll_not_add_and_remove() -> None:
    minter, first = first_version()
    rows = [*ROWS[1:], ["Stark Labs", "Elif Kaya", "$3.3M"]]
    second = align(first.doc, candidate_sheet(HEADERS, rows), minter)
    assert second.changes == [Scrolled("rows", "down", "Globex", "Stark Labs", 1)]


def test_title_change_is_reported() -> None:
    minter, first = first_version()
    second = align(first.doc, candidate_sheet(HEADERS, ROWS, title="Q4 Pipeline"), minter)
    assert second.changes == [TitleChanged("Q3 Pipeline", "Q4 Pipeline")]


def test_switch_to_code_resets_and_announces_once() -> None:
    minter, first = first_version()
    second = align(first.doc, candidate_code(["import os", "print(os.getcwd())"]), minter)
    assert second.doc.content_type == "code"
    assert len(second.changes) == 1 and isinstance(second.changes[0], ContentTypeChanged)
    assert second.doc.sheet is None


def test_code_line_edit_insert_and_ids() -> None:
    minter = IdMinter()
    lines = ["def f(x):", "    return x + 1", "", "print(f(2))"]
    first = align(None, candidate_code(lines), minter)
    edited = ["def f(x):", "    return x + 2", "", "print(f(2))"]
    second = align(first.doc, candidate_code(edited), minter)
    assert [ln.id for ln in second.doc.code.lines] == [ln.id for ln in first.doc.code.lines]  # type: ignore[union-attr]
    assert second.changes == [LineChanged("l2", "line 2", "    return x + 1", "    return x + 2", False, False)]
    inserted = ["def f(x):", "    # TODO", "    return x + 2", "", "print(f(2))"]
    third = align(second.doc, candidate_code(inserted), minter)
    assert next(c for c in third.changes if isinstance(c, LinesChanged)).texts == ("    # TODO",)


def test_summarize_code() -> None:
    minter = IdMinter()
    doc = align(None, candidate_code(["a", "b"]), minter).doc
    assert summarize(doc) == "Code python, 'app.py', 2 lines"
