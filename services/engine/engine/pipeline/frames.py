"""Decoding, cropping and change analysis of captured frames. Frames live only in memory."""

import io
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from PIL import Image, UnidentifiedImageError

from engine.model.document import Box
from engine.pipeline.geometry import make_box

ANALYSIS_WIDTH = 640
PIXEL_DELTA = 28
BLOCK = 8
GRID_X, GRID_Y = 16, 9


class BadFrameError(ValueError):
    pass


@dataclass(frozen=True)
class DecodedFrame:
    image: Image.Image
    gray: NDArray[np.uint8]

    @property
    def width(self) -> int:
        return self.image.width

    @property
    def height(self) -> int:
        return self.image.height


@dataclass(frozen=True)
class ChangeReport:
    fraction: float
    """Share of the 16x9 tiles inside the content box that changed."""
    bbox: Box | None
    """Bounding box of all changed blocks, frame coordinates."""
    blocks: int


def decode(data: bytes, max_pixels: int = 3840 * 2160) -> DecodedFrame:
    try:
        raw = Image.open(io.BytesIO(data))
        if raw.width * raw.height > max_pixels:
            raise BadFrameError("frame too large")
        image = raw.convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise BadFrameError(f"cannot decode frame: {exc}") from exc
    scale = ANALYSIS_WIDTH / image.width
    small = image.convert("L").resize((ANALYSIS_WIDTH, max(1, round(image.height * scale))), Image.Resampling.BILINEAR)
    return DecodedFrame(image=image, gray=np.asarray(small, dtype=np.uint8))


def _region(gray: NDArray[np.uint8], box: Box) -> NDArray[np.uint8]:
    h, w = gray.shape
    return gray[
        box.y0 * h // 1000 : max(box.y0 * h // 1000 + 1, box.y1 * h // 1000),
        box.x0 * w // 1000 : max(box.x0 * w // 1000 + 1, box.x1 * w // 1000),
    ]


def changed_blocks(a: NDArray[np.uint8], b: NDArray[np.uint8]) -> NDArray[np.bool_]:
    """Blocks of BLOCK x BLOCK analysis pixels where at least 3 pixels moved by PIXEL_DELTA."""
    h = min(a.shape[0], b.shape[0]) // BLOCK * BLOCK
    w = min(a.shape[1], b.shape[1]) // BLOCK * BLOCK
    if h == 0 or w == 0:
        return np.zeros((0, 0), dtype=bool)
    delta = np.abs(a[:h, :w].astype(np.int16) - b[:h, :w].astype(np.int16)) > PIXEL_DELTA
    counts = delta.reshape(h // BLOCK, BLOCK, w // BLOCK, BLOCK).sum(axis=(1, 3))
    result: NDArray[np.bool_] = counts >= 3
    return result


def compare(prev: DecodedFrame | None, cur: DecodedFrame, content: Box) -> ChangeReport:
    full = ChangeReport(fraction=1.0, bbox=content, blocks=-1)
    if prev is None or prev.gray.shape != cur.gray.shape:
        return full
    a, b = _region(prev.gray, content), _region(cur.gray, content)
    mask = changed_blocks(a, b)
    if mask.size == 0:
        return full
    n = int(mask.sum())
    if n == 0:
        return ChangeReport(fraction=0.0, bbox=None, blocks=0)
    rows, cols = mask.shape
    tiles = np.zeros((GRID_Y, GRID_X), dtype=bool)
    ys, xs = np.nonzero(mask)
    tiles[ys * GRID_Y // rows, xs * GRID_X // cols] = True
    cw, ch = content.x1 - content.x0, content.y1 - content.y0
    bbox = make_box(
        content.x0 + xs.min() / cols * cw,
        content.y0 + ys.min() / rows * ch,
        content.x0 + (xs.max() + 1) / cols * cw,
        content.y0 + (ys.max() + 1) / rows * ch,
    )
    return ChangeReport(fraction=float(tiles.mean()), bbox=bbox, blocks=n)


def same_frame(a: DecodedFrame, b: DecodedFrame, content: Box) -> bool:
    if a.gray.shape != b.gray.shape:
        return False
    mask = changed_blocks(_region(a.gray, content), _region(b.gray, content))
    return mask.size > 0 and not bool(mask.any())


def crop(frame: DecodedFrame, box: Box, *, upscale: float = 1.0) -> Image.Image:
    w, h = frame.width, frame.height
    left, top = box.x0 * w // 1000, box.y0 * h // 1000
    right, bottom = max(left + 1, box.x1 * w // 1000), max(top + 1, box.y1 * h // 1000)
    region = frame.image.crop((left, top, right, bottom))
    if upscale != 1.0:
        region = region.resize(
            (max(1, round(region.width * upscale)), max(1, round(region.height * upscale))),
            Image.Resampling.LANCZOS,
        )
    return region


def encode(image: Image.Image, fmt: str = "PNG") -> tuple[bytes, str]:
    buf = io.BytesIO()
    if fmt == "WEBP":
        image.save(buf, format="WEBP", quality=90)
        return buf.getvalue(), "image/webp"
    image.save(buf, format="PNG", optimize=False)
    return buf.getvalue(), "image/png"
