"""Compare two independent full reads of the same frame. Anything they disagree on, or that
only one read found, is marked uncertain. Text is always taken from the primary read."""

from dataclasses import dataclass
from difflib import SequenceMatcher

from engine.model.document import Block, Cell, Code, CodeLine, Document, Row, Sheet
from engine.pipeline.build import norm_text


@dataclass(frozen=True)
class CrossCheck:
    doc: Document
    compared: int
    disagreed: int


def _same(a: str, b: str) -> bool:
    return norm_text(a).replace(" ", "").lower() == norm_text(b).replace(" ", "").lower()


def _flag[T: (Cell, CodeLine, Block)](item: T) -> T:
    if item.unreadable or item.uncertain:
        return item
    return item.model_copy(update={"uncertain": True, "confidence": min(item.confidence, 0.5)})


def _check_cell(a: Cell, b: Cell | None) -> tuple[Cell, bool]:
    if b is None:
        return _flag(a), True
    if a.unreadable or b.unreadable:
        return (a if a.unreadable else _flag(a)), not (a.unreadable and b.unreadable)
    if not _same(a.text, b.text) or b.uncertain:
        return _flag(a), True
    return a, False


def _sheet(a: Sheet, b: Sheet) -> tuple[Sheet, int, int]:
    compared = disagreed = 0
    cols = SequenceMatcher(
        a=[norm_text(c.text).lower() for c in a.columns],
        b=[norm_text(c.text).lower() for c in b.columns],
        autojunk=False,
    )
    col_map: dict[int, int] = {}
    for tag, i1, i2, j1, j2 in cols.get_opcodes():
        if tag in ("equal", "replace"):
            for k in range(min(i2 - i1, j2 - j1)):
                col_map[i1 + k] = j1 + k
    columns: list[Cell] = []
    for i, col in enumerate(a.columns):
        other = b.columns[col_map[i]] if i in col_map else None
        checked, bad = _check_cell(col, other)
        columns.append(checked)
        compared += 1
        disagreed += bad
    keys_a = [norm_text(r.key or "").lower() or f"#{i}" for i, r in enumerate(a.rows)]
    keys_b = [norm_text(r.key or "").lower() or f"#{i}" for i, r in enumerate(b.rows)]
    row_map: dict[int, int] = {}
    for tag, i1, i2, j1, j2 in SequenceMatcher(a=keys_a, b=keys_b, autojunk=False).get_opcodes():
        if tag in ("equal", "replace"):
            for k in range(min(i2 - i1, j2 - j1)):
                row_map[i1 + k] = j1 + k
    rows: list[Row] = []
    for i, row in enumerate(a.rows):
        other_row = b.rows[row_map[i]] if i in row_map else None
        cells: list[Cell] = []
        for j, cell in enumerate(row.cells):
            other = None
            if other_row is not None and j in col_map and col_map[j] < len(other_row.cells):
                other = other_row.cells[col_map[j]]
            checked, bad = _check_cell(cell, other)
            cells.append(checked)
            compared += 1
            disagreed += bad
        rows.append(row.model_copy(update={"cells": cells}))
    return a.model_copy(update={"columns": columns, "rows": rows}), compared, disagreed


def _code(a: Code, b: Code) -> tuple[Code, int, int]:
    pairs: dict[int, int] = {}
    m = SequenceMatcher(a=[ln.text.strip() for ln in a.lines], b=[ln.text.strip() for ln in b.lines], autojunk=False)
    for tag, i1, i2, j1, j2 in m.get_opcodes():
        if tag in ("equal", "replace"):
            for k in range(min(i2 - i1, j2 - j1)):
                pairs[i1 + k] = j1 + k
    lines: list[CodeLine] = []
    disagreed = 0
    for i, line in enumerate(a.lines):
        other = b.lines[pairs[i]] if i in pairs else None
        bad = (
            other is None
            or other.uncertain
            or other.unreadable != line.unreadable
            or line.text.rstrip() != other.text.rstrip()
        )
        lines.append(_flag(line) if bad and not line.unreadable else line)
        disagreed += bad
    return a.model_copy(update={"lines": lines}), len(a.lines), disagreed


def cross_check(primary: Document, second: Document) -> CrossCheck:
    """Both documents must be built from reads of the same image."""
    if primary.sheet is not None and second.sheet is not None:
        sheet, n, bad = _sheet(primary.sheet, second.sheet)
        return CrossCheck(primary.model_copy(update={"sheet": sheet}), n, bad)
    if primary.code is not None and second.code is not None:
        code, n, bad = _code(primary.code, second.code)
        return CrossCheck(primary.model_copy(update={"code": code}), n, bad)
    if primary.sheet is not None:
        sheet = primary.sheet.model_copy(
            update={
                "columns": [_flag(c) for c in primary.sheet.columns],
                "rows": [r.model_copy(update={"cells": [_flag(c) for c in r.cells]}) for r in primary.sheet.rows],
            }
        )
        n = len(sheet.columns) + sum(len(r.cells) for r in sheet.rows)
        return CrossCheck(primary.model_copy(update={"sheet": sheet}), n, n)
    if primary.code is not None:
        code = primary.code.model_copy(update={"lines": [_flag(ln) for ln in primary.code.lines]})
        return CrossCheck(primary.model_copy(update={"code": code}), len(code.lines), len(code.lines))
    if primary.blocks:
        others = second.blocks or []
        pairs: dict[int, int] = {}
        matcher = SequenceMatcher(
            a=[(b.kind, norm_text(b.text)) for b in primary.blocks],
            b=[(b.kind, norm_text(b.text)) for b in others],
            autojunk=False,
        )
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag in ("equal", "replace"):
                pairs.update({i1 + k: j1 + k for k in range(min(i2 - i1, j2 - j1))})
        blocks: list[Block] = []
        bad_count = 0
        for i, block in enumerate(primary.blocks):
            other = others[pairs[i]] if i in pairs else None
            bad = (
                other is None
                or other.uncertain
                or other.unreadable
                or block.kind != other.kind
                or norm_text(block.text) != norm_text(other.text)
            )
            blocks.append(_flag(block) if bad else block)
            bad_count += bad
        return CrossCheck(primary.model_copy(update={"blocks": blocks}), len(blocks), bad_count)
    return CrossCheck(primary, 0, 0)
