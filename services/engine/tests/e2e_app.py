"""Engine for the browser loop test (apps/web/tests/loop.spec.ts). Not the product.

The vision model here is scripted: it answers from the fixture's ground truth, which the test
posts to /test/truth before feeding each frame. Everything else (WebSocket protocol, change
analysis, cross-check, alignment, diff, announcements, pointer) is the shipped engine. The
model's own accuracy is measured separately, against real Gemini responses, in bench/.

Run: uv run uvicorn tests.e2e_app:app --port 8788
"""

from typing import Any

from fastapi import Body

from engine.api.app import create_app
from engine.config import Settings
from engine.llm.client import Usage, VisionRequest, VisionResult
from engine.llm.schemas import AskAnswer, FullRead, ReadCode, ReadColumn, ReadLine, ReadRow, ReadSheet

EMPTY_SHEET = ReadSheet(sheet_name="", columns=[], rows=[], unclear=[])
EMPTY_CODE = ReadCode(file_name="", language="", x_range=[0, 0], lines=[], unclear=[])


def _x(box: dict[str, int]) -> list[int]:
    return [box["x0"], box["x1"]]


def _y(box: dict[str, int]) -> list[int]:
    return [box["y0"], box["y1"]]


def read_from_truth(truth: dict[str, Any]) -> FullRead:
    boxes = truth["boxes"]
    if truth["content_type"] == "sheet":
        t = truth["sheet"]
        sheet = ReadSheet(
            sheet_name=t["sheet_name"],
            columns=[ReadColumn(header=h, x_range=_x(boxes[f"h{j}"])) for j, h in enumerate(t["columns"])],
            rows=[ReadRow(y_range=_y(boxes[f"r{i}c0"]), cells=list(r)) for i, r in enumerate(t["rows"])],
            unclear=[],
        )
        return FullRead(
            content_type="sheet",
            title=truth["title"],
            content_box_2d=[0, 0, 1000, 1000],
            sheet=sheet,
            code=EMPTY_CODE,
            blocks=[],
        )
    t = truth["code"]
    lines = [
        ReadLine(n=ln["n"], text=ln["text"], y_range=_y(boxes[f"l{ln['n']}"]))
        for ln in t["lines"]
        if f"l{ln['n']}" in boxes
    ]
    xs = [boxes[f"l{ln.n}"]["x0"] for ln in lines] or [0]
    code = ReadCode(file_name=t["file_name"], language=t["language"], x_range=[min(xs), 1000], lines=lines, unclear=[])
    return FullRead(
        content_type="code",
        title=truth["title"],
        content_box_2d=[0, 0, 1000, 1000],
        sheet=EMPTY_SHEET,
        code=code,
        blocks=[],
    )


class TruthModel:
    def __init__(self) -> None:
        self.truth: dict[str, Any] | None = None
        self.calls = 0

    async def generate(self, request: VisionRequest) -> VisionResult:
        self.calls += 1
        if request.purpose == "ask":
            body = AskAnswer(answer="Scripted answer for the loop test.", refs=[]).model_dump_json()
        else:
            assert self.truth is not None, "post /test/truth before sending frames"
            body = read_from_truth(self.truth).model_dump_json()
        return VisionResult(text=body, model="scripted-truth", usage=Usage(), latency_ms=0)


model = TruthModel()
settings = Settings(
    gemini_api_key=None,
    llm_mode="replay",
    full_reconstruct_threshold=0.0,
    allowed_origins=["http://localhost:4173", "http://localhost:5173"],
    frames_per_minute=600,
)
app = create_app(settings, model)


@app.post("/test/truth")
async def set_truth(truth: dict[str, Any] = Body(...)) -> dict[str, int]:  # noqa: B008
    model.truth = truth
    return {"calls": model.calls}
