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


async def _score(frame: Path) -> tuple[int, int, int]:
    """-> (cells, exact, confidently wrong) for one frame, replayed through the real pipeline."""
    truth = json.loads(frame.with_suffix(".truth.json").read_text())
    settings = Settings(gemini_api_key=None, llm_mode="replay", golden_dir=RESPONSES)
    pipe = SessionPipeline(ReplayVisionModel(RESPONSES), settings)
    out = await pipe.process(frame.read_bytes())
    assert out.doc is not None and out.doc.sheet is not None
    assert out.announces[0].kind == "content_type"
    assert pipe.meter.calls == 2, "expected a recorded reconstruct and cross-check"
    sheet = out.doc.sheet
    got = [list(sheet.columns), *[list(r.cells) for r in sheet.rows]]
    exact = wrong = 0
    cells = _cells(truth)
    for i, j, v in cells:
        cell = got[i][j] if i < len(got) and j < len(got[i]) else None
        if cell is not None and _norm(cell.text) == v:
            exact += 1
        elif cell is not None and not (cell.uncertain or cell.unreadable):
            wrong += 1
    return len(cells), exact, wrong


@pytest.mark.skipif(not CASES, reason="no golden frames committed")
async def test_recorded_reconstructions_meet_the_kill_test_bar() -> None:
    """Same bar as the Day-1 kill test, over all golden frames: >= 90% exact, <= 2% confidently wrong."""
    scores = [await _score(f) for f in CASES]
    cells = sum(s[0] for s in scores)
    assert sum(s[1] for s in scores) / cells >= 0.9
    assert sum(s[2] for s in scores) / cells <= 0.02
