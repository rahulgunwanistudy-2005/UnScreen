"""A scripted vision model and synthetic frames, so pipeline tests never call a real API."""

import io
from collections import defaultdict, deque

from PIL import Image, ImageDraw
from pydantic import BaseModel

from engine.llm.client import ModelError, Usage, VisionRequest, VisionResult


class ScriptedModel:
    def __init__(self) -> None:
        self.queues: dict[str, deque[BaseModel | Exception]] = defaultdict(deque)
        self.calls: list[VisionRequest] = []

    def push(self, purpose: str, *responses: BaseModel | Exception) -> None:
        self.queues[purpose].extend(responses)

    def purposes(self) -> list[str]:
        return [c.purpose for c in self.calls]

    async def generate(self, request: VisionRequest) -> VisionResult:
        self.calls.append(request)
        queue = self.queues[request.purpose]
        if not queue:
            raise ModelError(f"no scripted response for {request.purpose}")
        item = queue.popleft()
        if isinstance(item, Exception):
            raise item
        return VisionResult(
            text=item.model_dump_json(), model="gemini-3.8-flash", usage=Usage(1000, 200, 50), latency_ms=5
        )


def sheet_frame(rows: list[list[str]], size: tuple[int, int] = (1000, 600), marker: str = "") -> bytes:
    """Rows drawn on a grid that matches tests.factories.full_sheet_read's coordinates."""
    w, h = size
    img = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(img)
    cols = len(rows[0]) if rows else 1
    for i, values in enumerate(rows):
        y0 = (100 + i * 50) * h // 1000
        for j, v in enumerate(values):
            x0 = j * (1000 // cols) * w // 1000
            draw.rectangle([x0, y0, x0 + w // cols, y0 + 50 * h // 1000], outline="gray")
            draw.text((x0 + 8, y0 + 6), v * 3, fill="black")
    if marker:
        draw.rectangle([0, 0, 200, 40], fill="black")
        draw.text((10, 10), marker, fill="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
