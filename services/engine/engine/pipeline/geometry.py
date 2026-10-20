"""Box arithmetic. Every box here is normalised 0..1000 of the full captured frame."""

from collections.abc import Sequence

from engine.model.document import Box


def clamp(v: float) -> int:
    return max(0, min(1000, round(v)))


def make_box(x0: float, y0: float, x1: float, y1: float) -> Box:
    a, b = sorted((clamp(x0), clamp(x1)))
    c, d = sorted((clamp(y0), clamp(y1)))
    return Box(x0=a, y0=c, x1=b, y1=d)


def from_box_2d(b: Sequence[int], within: Box) -> Box:
    """Gemini's [ymin, xmin, ymax, xmax] relative to the image `within` -> frame box."""
    ymin, xmin, ymax, xmax = (b[0], b[1], b[2], b[3]) if len(b) == 4 else (0, 0, 1000, 1000)
    return make_box(map_x(xmin, within), map_y(ymin, within), map_x(xmax, within), map_y(ymax, within))


def map_x(v: float, within: Box) -> float:
    return within.x0 + (max(0.0, min(1000.0, v)) / 1000) * (within.x1 - within.x0)


def map_y(v: float, within: Box) -> float:
    return within.y0 + (max(0.0, min(1000.0, v)) / 1000) * (within.y1 - within.y0)


def area(b: Box) -> int:
    return max(0, b.x1 - b.x0) * max(0, b.y1 - b.y0)


def intersects(a: Box, b: Box) -> bool:
    return a.x0 < b.x1 and b.x0 < a.x1 and a.y0 < b.y1 and b.y0 < a.y1


def union(boxes: Sequence[Box]) -> Box | None:
    if not boxes:
        return None
    return Box(
        x0=min(b.x0 for b in boxes),
        y0=min(b.y0 for b in boxes),
        x1=max(b.x1 for b in boxes),
        y1=max(b.y1 for b in boxes),
    )


def pad(b: Box, dx: float, dy: float) -> Box:
    return make_box(b.x0 - dx, b.y0 - dy, b.x1 + dx, b.y1 + dy)


def contains_point(b: Box, x: int, y: int) -> bool:
    return b.x0 <= x <= b.x1 and b.y0 <= y <= b.y1


def distance_to(b: Box, x: int, y: int) -> float:
    dx = max(b.x0 - x, 0, x - b.x1)
    dy = max(b.y0 - y, 0, y - b.y1)
    return float((dx * dx + dy * dy) ** 0.5)
