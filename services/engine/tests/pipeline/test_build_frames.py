from engine.llm.schemas import Unclear
from engine.model.document import Box
from engine.pipeline.build import build_document, norm_text
from engine.pipeline.frames import compare, decode, same_frame
from engine.pipeline.geometry import from_box_2d
from engine.pipeline.pointer import describe_pointer
from tests.factories import full_sheet_read, full_slide_read
from tests.fakes import sheet_frame

FULL = Box(x0=0, y0=0, x1=1000, y1=1000)


def test_box_2d_is_ymin_xmin_ymax_xmax_relative_to_crop() -> None:
    within = Box(x0=100, y0=200, x1=600, y1=700)
    b = from_box_2d([0, 0, 1000, 500], within)
    assert (b.x0, b.y0, b.x1, b.y1) == (100, 200, 350, 700)


def test_unreadable_and_unsure_cells_carry_flags_not_text() -> None:
    read = full_sheet_read(["A", "B"], [["x", "y"]])
    read.sheet.rows[0].cells[0] = "ghost"
    read.sheet.rows[0].cells[1] = "7?"
    read.sheet.unclear = [Unclear(row=0, col=0, legibility="unreadable"), Unclear(row=0, col=1, legibility="unsure")]
    doc = build_document(read, FULL)
    a, b = doc.sheet.rows[0].cells  # type: ignore[union-attr]
    assert a.unreadable and a.text == "" and a.confidence == 0.0
    assert b.uncertain and b.text == "7?"
    assert doc.sheet.rows[0].key is None  # type: ignore[union-attr]


def test_short_rows_are_padded_and_sheet_without_columns_falls_back() -> None:
    read = full_sheet_read(["A", "B", "C"], [["x"]])
    doc = build_document(read, FULL)
    assert [c.text for c in doc.sheet.rows[0].cells] == ["x", "", ""]  # type: ignore[union-attr]
    empty = full_sheet_read([], [])
    assert build_document(empty, FULL).content_type == "unknown"


def test_slide_blocks() -> None:
    doc = build_document(full_slide_read(["Sprint review", "Shipped export"]), FULL)
    assert doc.content_type == "slide"
    assert [(b.kind, b.level) for b in doc.blocks or []] == [("heading", 1), ("list_item", None)]


def test_norm_text() -> None:
    assert norm_text("  a  b \n c ") == "a b c"


def test_change_detection_finds_the_edited_cell() -> None:
    rows = [["Acme", "Asha", "$1.1M"], ["Globex", "Ben", "$0.4M"]]
    a = decode(sheet_frame(rows))
    rows[0][2] = "$9.9M"
    b = decode(sheet_frame(rows))
    assert same_frame(a, a, FULL) and not same_frame(a, b, FULL)
    report = compare(a, b, FULL)
    assert 0 < report.fraction < 0.1
    assert report.bbox is not None and report.bbox.x0 >= 600 and report.bbox.y1 <= 160
    assert compare(None, b, FULL).fraction == 1.0


def test_pointer_without_document_and_outside_content() -> None:
    assert describe_pointer(None, 1, 1) == (None, "Nothing is being read yet.")
    doc = build_document(full_slide_read(["Title"]), Box(x0=100, y0=100, x1=900, y1=900))
    doc = doc.model_copy(update={"content_bbox": Box(x0=100, y0=100, x1=900, y1=900)})
    assert describe_pointer(doc, 5, 5)[1] == "The pointer is outside the shared content."
