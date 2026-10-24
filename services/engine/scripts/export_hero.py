"""Export the landing-page hero from a real recorded reconstruction.

Replays a golden frame through the shipped pipeline (recorded Gemini responses, no live call)
and writes the cropped frame plus every reconstructed cell, its box and the real announcement.

Usage: uv run python scripts/export_hero.py sheet-105-1080p-degraded
"""

import asyncio
import json
import sys
from pathlib import Path

from PIL import Image

from engine.config import Settings
from engine.llm.client import ReplayVisionModel
from engine.model.document import Box
from engine.pipeline.geometry import pad, union
from engine.pipeline.session import SessionPipeline

ENGINE = Path(__file__).resolve().parents[1]
GOLDEN = ENGINE / "tests" / "golden"
WEB = ENGINE.parents[1] / "apps" / "web"


def rel(b: Box, crop: Box) -> dict[str, float]:
    w, h = crop.x1 - crop.x0, crop.y1 - crop.y0
    return {
        "x": round((b.x0 - crop.x0) / w, 4),
        "y": round((b.y0 - crop.y0) / h, 4),
        "w": round((b.x1 - b.x0) / w, 4),
        "h": round((b.y1 - b.y0) / h, 4),
    }


async def main(frame_id: str) -> None:
    frame = GOLDEN / "frames" / f"{frame_id}.jpg"
    settings = Settings(gemini_api_key=None, llm_mode="replay", golden_dir=GOLDEN / "responses")
    pipe = SessionPipeline(ReplayVisionModel(settings.golden_dir), settings)
    out = await pipe.process(frame.read_bytes())
    doc = out.doc
    assert doc is not None and doc.sheet is not None, "hero needs a sheet"
    boxes = [c.bbox for c in doc.sheet.columns] + [c.bbox for r in doc.sheet.rows for c in r.cells]
    table = union(boxes)
    assert table is not None
    crop = pad(table, 12, 24)
    with Image.open(frame) as img:
        w, h = img.size
        box = (crop.x0 * w // 1000, crop.y0 * h // 1000, crop.x1 * w // 1000, crop.y1 * h // 1000)
        region = img.convert("RGB").crop(box)
        static = WEB / "static" / "hero"
        static.mkdir(parents=True, exist_ok=True)
        region.save(static / "frame.jpg", quality=92)
        size = region.size
    data = {
        "source": f"services/engine/tests/golden/frames/{frame_id}.jpg",
        "image": {"src": "/hero/frame.jpg", "width": size[0], "height": size[1]},
        "title": doc.title,
        "announcement": out.announces[0].text if out.announces else "",
        "columns": [{"text": c.text, "box": rel(c.bbox, crop)} for c in doc.sheet.columns],
        "rows": [
            {
                "key": r.key,
                "cells": [{"text": c.text, "box": rel(c.bbox, crop), "uncertain": c.uncertain} for c in r.cells],
            }
            for r in doc.sheet.rows
        ],
    }
    target = WEB / "src" / "lib" / "hero" / "hero.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {target} and {static / 'frame.jpg'} ({size[0]}x{size[1]})")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "sheet-105-1080p-degraded"))
