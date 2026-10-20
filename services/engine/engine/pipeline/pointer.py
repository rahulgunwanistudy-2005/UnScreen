"""Map the presenter's pointer to the cell, line or block under it."""

from engine.model.document import Box, Document
from engine.pipeline.geometry import contains_point, distance_to

NEAR = 25


def _value(text: str, unreadable: bool, uncertain: bool) -> str:
    if unreadable:
        return "unreadable"
    if uncertain:
        return f"{text or 'blank'} (unclear)"
    return text or "blank"


def describe_pointer(doc: Document | None, x: int, y: int) -> tuple[str | None, str]:
    """-> (ref, spoken text)"""
    if doc is None:
        return None, "Nothing is being read yet."
    if not contains_point(doc.content_bbox, x, y):
        return None, "The pointer is outside the shared content."
    candidates: list[tuple[float, str, str]] = []

    def consider(box: Box, ref: str, text: str) -> None:
        d = 0.0 if contains_point(box, x, y) else distance_to(box, x, y)
        if d <= NEAR:
            candidates.append((d, ref, text))

    if doc.sheet:
        for j, col in enumerate(doc.sheet.columns):
            consider(col.bbox, col.id, f"Column header {j + 1}: {_value(col.text, col.unreadable, col.uncertain)}")
        for i, row in enumerate(doc.sheet.rows):
            label = row.key or f"row {i + 1}"
            for j, cell in enumerate(row.cells):
                col_name = doc.sheet.columns[j].text if j < len(doc.sheet.columns) else f"column {j + 1}"
                consider(
                    cell.bbox, cell.id, f"{label}, {col_name}: {_value(cell.text, cell.unreadable, cell.uncertain)}"
                )
    if doc.code:
        for i, line in enumerate(doc.code.lines):
            n = line.n if line.n is not None else i + 1
            consider(line.bbox, line.id, f"Line {n}: {_value(line.text.strip(), line.unreadable, line.uncertain)}")
    for block in doc.blocks or []:
        consider(
            block.bbox,
            block.id,
            f"{block.kind.replace('_', ' ').capitalize()}: {_value(block.text, block.unreadable, block.uncertain)}",
        )
    if not candidates:
        return None, "The pointer is not on any text."
    _, ref, text = min(candidates, key=lambda c: c[0])
    return ref, f"Pointer is on {text}"
