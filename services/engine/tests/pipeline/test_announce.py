from engine.pipeline.announce import announcements
from engine.pipeline.changes import CellChanged, ContentTypeChanged, LineChanged, RowsChanged, Scrolled


def cell(n: int, *, uncertain: bool = False, unreadable: bool = False) -> CellChanged:
    return CellChanged(f"r{n}.c3", f"r{n}", "c3", f"Row{n}", "Q3 revenue", "$1.1M", "$1.2M", uncertain, unreadable)


def test_value_change_old_to_new_and_new_only() -> None:
    [a] = announcements([cell(1)], 2, "old_to_new", None)
    assert a.text == "Row1, Q3 revenue: $1.1M to $1.2M."
    assert a.priority == "other" and a.refs == ["r1.c3"]
    [b] = announcements([cell(1)], 2, "new_only", None)
    assert b.text == "Row1, Q3 revenue: $1.2M."


def test_uncertain_value_is_never_spoken() -> None:
    [a] = announcements([cell(1, uncertain=True)], 2, "old_to_new", None)
    assert a.text == "Row1, Q3 revenue: possibly changed, unclear."
    assert "$1.2M" not in a.text and a.kind == "uncertain"
    [b] = announcements([cell(1, unreadable=True)], 2, "old_to_new", None)
    assert b.text == "Row1, Q3 revenue: changed, now unreadable."


def test_focus_row_is_prioritised() -> None:
    out = announcements([cell(1), cell(2)], 2, "old_to_new", "r2")
    assert out[0].priority == "focus" and out[0].refs == ["r2.c3"]


def test_content_type_first_and_many_cells_coalesce() -> None:
    changes = [cell(i) for i in range(1, 9)]
    switch = ContentTypeChanged("none", "sheet", "Q3", "Spreadsheet, 'Q3', 8 rows, 3 columns")
    out = announcements([*changes, switch], 2, "old_to_new", None)
    assert out[0].kind == "content_type"
    assert out[0].text == "Now showing: Spreadsheet, 'Q3', 8 rows, 3 columns."
    assert [a.text for a in out[1:]] == ["8 cells changed."]


def test_rows_scroll_and_lines() -> None:
    added = announcements([RowsChanged("added", ("r5",), ("Stark Labs",))], 3, "old_to_new", None)
    assert added[0].text == "Row added: Stark Labs." and added[0].kind == "row_added"
    many = announcements([RowsChanged("removed", ("a", "b", "c", "d"), ("A", "B", "C", "D"))], 3, "old_to_new", None)
    assert many[0].text == "4 rows removed: A, B, C and 1 more."
    scroll = announcements([Scrolled("rows", "down", "Globex", "Stark Labs", 2)], 3, "old_to_new", None)
    assert scroll[0].text == "Scrolled down 2 rows. Now showing Globex to Stark Labs."
    line = announcements([LineChanged("l2", "line 2", "x = 1", "x = 2", False, False)], 3, "new_only", None)
    assert line[0].text == "Line 2 now reads: x = 2"
