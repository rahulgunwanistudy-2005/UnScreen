import pytest

from engine.config import Settings
from engine.llm.client import ModelError
from engine.llm.schemas import Reading, RegionRow, SheetRegionRead, VerifyRead
from engine.pipeline.frames import BadFrameError
from engine.pipeline.session import SessionPipeline
from tests.factories import full_code_read, full_sheet_read
from tests.fakes import ScriptedModel, sheet_frame

HEADERS = ["Account", "Owner", "Q3 revenue"]
ROWS = [
    ["Acme Corp", "Asha Rao", "$1.1M"],
    ["Globex", "Ben Okafor", "$0.4M"],
    ["Initech", "Chen Wei", "$2.0M"],
]


def make() -> tuple[ScriptedModel, SessionPipeline]:
    model = ScriptedModel()
    return model, SessionPipeline(model, Settings(gemini_api_key=None, llm_mode="replay"))


def edited(r: int, c: int, value: str) -> list[list[str]]:
    rows = [row[:] for row in ROWS]
    rows[r][c] = value
    return rows


async def test_first_frame_builds_document_and_announces_it() -> None:
    model, pipe = make()
    model.push("reconstruct", full_sheet_read(HEADERS, ROWS))
    out = await pipe.process(sheet_frame(ROWS))
    assert out.mode == "full" and out.doc is not None and out.doc.version == 1
    assert [a.text for a in out.announces] == ["Now showing: Spreadsheet, 'Q3 Pipeline', 3 rows, 3 columns."]
    assert model.purposes() == ["reconstruct"]


async def test_identical_frame_costs_nothing() -> None:
    model, pipe = make()
    model.push("reconstruct", full_sheet_read(HEADERS, ROWS))
    frame = sheet_frame(ROWS)
    await pipe.process(frame)
    out = await pipe.process(frame)
    assert out.mode == "unchanged" and out.announces == []
    assert model.purposes() == ["reconstruct"]


async def test_small_edit_uses_region_read_and_verification_in_parallel() -> None:
    model, pipe = make()
    model.push("reconstruct", full_sheet_read(HEADERS, ROWS))
    await pipe.process(sheet_frame(ROWS))
    model.push("region_sheet", SheetRegionRead(rows=[RegionRow(cells=["$1.2M"])], unclear=[]))
    model.push("verify_cell", VerifyRead(readings=[Reading(text="$1.2M", legibility="clear")]))
    out = await pipe.process(sheet_frame(edited(0, 2, "$1.2M")))
    assert out.mode == "region"
    assert sorted(model.purposes()[1:]) == ["region_sheet", "verify_cell"]
    assert [a.text for a in out.announces] == ["Acme Corp, Q3 revenue: $1.1M to $1.2M."]
    assert [(o.op, o.path, o.value) for o in out.ops if o.path != "/version"] == [
        ("replace", "/sheet/rows/0/cells/2/text", "$1.2M")
    ]


async def test_disagreeing_reads_become_uncertain_and_are_not_spoken_as_values() -> None:
    model, pipe = make()
    model.push("reconstruct", full_sheet_read(HEADERS, ROWS))
    await pipe.process(sheet_frame(ROWS))
    model.push("region_sheet", SheetRegionRead(rows=[RegionRow(cells=["$1.2M"])], unclear=[]))
    model.push("verify_cell", VerifyRead(readings=[Reading(text="$7.2M", legibility="clear")]))
    out = await pipe.process(sheet_frame(edited(0, 2, "$1.2M")))
    assert [a.text for a in out.announces] == ["Acme Corp, Q3 revenue: possibly changed, unclear."]
    cell = out.doc.sheet.rows[0].cells[2]  # type: ignore[union-attr]
    assert cell.uncertain and cell.confidence < 0.9


async def test_region_mismatch_falls_back_to_full_read_then_verifies() -> None:
    model, pipe = make()
    model.push("reconstruct", full_sheet_read(HEADERS, ROWS))
    await pipe.process(sheet_frame(ROWS))
    model.push("region_sheet", SheetRegionRead(rows=[], unclear=[]))
    model.push("verify_cell", VerifyRead(readings=[Reading(text="$1.2M", legibility="clear")]))
    model.push("reconstruct", full_sheet_read(HEADERS, edited(0, 2, "$1.2M")))
    model.push("verify_cell", VerifyRead(readings=[Reading(text="$1.2M", legibility="clear")]))
    out = await pipe.process(sheet_frame(edited(0, 2, "$1.2M")))
    assert out.mode == "full"
    assert [a.text for a in out.announces] == ["Acme Corp, Q3 revenue: $1.1M to $1.2M."]


async def test_reverting_to_a_cached_frame_needs_no_model_call() -> None:
    model, pipe = make()
    model.push("reconstruct", full_sheet_read(HEADERS, ROWS))
    await pipe.process(sheet_frame(ROWS))
    model.push("region_sheet", SheetRegionRead(rows=[RegionRow(cells=["$1.2M"])], unclear=[]))
    model.push("verify_cell", VerifyRead(readings=[Reading(text="$1.2M", legibility="clear")]))
    await pipe.process(sheet_frame(edited(0, 2, "$1.2M")))
    calls = len(model.calls)
    out = await pipe.process(sheet_frame(ROWS))
    assert out.mode == "cache" and len(model.calls) == calls
    assert [a.text for a in out.announces] == ["Acme Corp, Q3 revenue: $1.2M to $1.1M."]


async def test_content_switch_announces_new_type() -> None:
    model, pipe = make()
    model.push("reconstruct", full_sheet_read(HEADERS, ROWS))
    await pipe.process(sheet_frame(ROWS))
    model.push("reconstruct", full_code_read(["import os", "print(os.name)"]))
    out = await pipe.process(sheet_frame([["x", "y", "z"]] * 8, marker="code"))
    assert out.doc is not None and out.doc.content_type == "code"
    assert out.announces[0].text == "Now showing: Code python, 'app.py', 2 lines."


async def test_model_failure_propagates_and_state_is_kept() -> None:
    model, pipe = make()
    model.push("reconstruct", full_sheet_read(HEADERS, ROWS))
    await pipe.process(sheet_frame(ROWS))
    model.push("reconstruct", ModelError("boom", retryable=True))
    with pytest.raises(ModelError):
        await pipe.process(sheet_frame([["a", "b", "c"]] * 9, marker="x"))
    assert pipe.doc is not None and pipe.doc.version == 1


async def test_bad_frame_is_rejected() -> None:
    _, pipe = make()
    with pytest.raises(BadFrameError):
        await pipe.process(b"not an image")


async def test_pointer_maps_to_cell() -> None:
    model, pipe = make()
    model.push("reconstruct", full_sheet_read(HEADERS, ROWS))
    await pipe.process(sheet_frame(ROWS))
    ref, text = pipe.map_pointer(800, 120)
    assert ref == "r1.c3"
    assert text == "Pointer is on Acme Corp, Q3 revenue: $1.1M"
