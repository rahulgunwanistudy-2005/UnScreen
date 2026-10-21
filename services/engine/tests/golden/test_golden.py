"""Replays recorded Gemini responses for committed fixture frames through the real pipeline.

CI never calls the live API. To refresh: copy frames into tests/golden/frames (with their
.truth.json), run the benchmark with UNSCREEN_LLM_MODE=record, and commit both."""

import json
from pathlib import Path
from typing import Any

import pytest

from engine.config import Settings
from engine.llm.client import ReplayVisionModel
from engine.pipeline.session import SessionPipeline

HERE = Path(__file__).resolve().parent
FRAMES = HERE / "frames"
RESPONSES = HERE / "responses"
CASES = sorted(p for p in FRAMES.glob("*.jpg")) if FRAMES.exists() else []


def _norm(s: str) -> str:
    return " ".join(s.split())


def _cells(truth: dict[str, Any]) -> list[tuple[int, int, str]]:
    rows = [truth["sheet"]["columns"], *truth["sheet"]["rows"]]
    return [(i, j, _norm(v)) for i, r in enumerate(rows) for j, v in enumerate(r)]


@pytest.mark.skipif(not CASES, reason="no golden frames committed")
@pytest.mark.parametrize("frame", CASES, ids=[p.stem for p in CASES])
async def test_recorded_reconstruction_matches_truth(frame: Path) -> None:
    truth = json.loads(frame.with_suffix(".truth.json").read_text())
    settings = Settings(gemini_api_key=None, llm_mode="replay", golden_dir=RESPONSES)
    pipe = SessionPipeline(ReplayVisionModel(RESPONSES), settings)
    out = await pipe.process(frame.read_bytes())
    assert out.doc is not None and out.doc.sheet is not None
    assert out.announces[0].kind == "content_type"
    sheet = out.doc.sheet
    got = [[c.text for c in sheet.columns], *[[c.text for c in r.cells] for r in sheet.rows]]
    cells = _cells(truth)
    exact = sum(1 for i, j, v in cells if i < len(got) and j < len(got[i]) and _norm(got[i][j]) == v)
    assert exact / len(cells) >= 0.9
    confident_wrong = sum(
        1
        for i, j, v in cells
        if i < len(got)
        and j < len(got[i])
        and _norm(got[i][j]) != v
        and not (sheet.rows[i - 1].cells[j] if i else sheet.columns[j]).uncertain
    )
    assert confident_wrong / len(cells) <= 0.02
