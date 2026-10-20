"""Give a candidate document stable ids by matching it against the previous version, and
report what changed. Ids are minted once per session and never regenerated."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import TypeVar

from engine.model.document import Block, Cell, Code, CodeLine, Document, Row, Sheet
from engine.pipeline.changes import (
    BlockChanged,
    BlocksChanged,
    CellChanged,
    Change,
    ContentTypeChanged,
    LineChanged,
    LinesChanged,
    RowsChanged,
    Scrolled,
    TitleChanged,
)

T = TypeVar("T")
ROW_SIMILARITY = 0.5


@dataclass
class IdMinter:
    counters: dict[str, int] = field(default_factory=dict)

    def mint(self, prefix: str) -> str:
        n = self.counters.get(prefix, 0) + 1
        self.counters[prefix] = n
        return f"{prefix}{n}"


@dataclass(frozen=True)
class Alignment:
    doc: Document
    changes: list[Change]


def _key(text: str | None) -> str:
    return " ".join((text or "").lower().split())


def match[T](
    old: Sequence[T],
    new: Sequence[T],
    key: Callable[[T], str],
    similar: Callable[[T, T], bool],
) -> dict[int, int]:
    """new index -> old index. Exact key runs first (LCS), then same-length gaps pair by
    position when `similar` agrees."""
    matcher = SequenceMatcher(a=[key(o) for o in old], b=[key(n) for n in new], autojunk=False)
    pairs: dict[int, int] = {}
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                pairs[j1 + k] = i1 + k
        elif tag == "replace":
            for k in range(min(i2 - i1, j2 - j1)):
                if similar(old[i1 + k], new[j1 + k]):
                    pairs[j1 + k] = i1 + k
    return pairs


def _scroll(old_count: int, new_count: int, pairs: dict[int, int]) -> tuple[str, int] | None:
    """Detect a viewport shift: rows leave one end and arrive at the other."""
    if not pairs:
        return None
    matched_old = sorted(pairs.values())
    matched_new = sorted(pairs)
    removed_top = matched_old[0]
    removed_bottom = old_count - 1 - matched_old[-1]
    added_top = matched_new[0]
    added_bottom = new_count - 1 - matched_new[-1]
    contiguous = matched_old[-1] - matched_old[0] + 1 == len(pairs) == matched_new[-1] - matched_new[0] + 1
    if not contiguous:
        return None
    if removed_top > 0 and added_bottom > 0 and removed_bottom == 0 and added_top == 0:
        return "down", removed_top
    if removed_bottom > 0 and added_top > 0 and removed_top == 0 and added_bottom == 0:
        return "up", added_top
    return None


def _cell_label(cell: Cell) -> str:
    if cell.unreadable:
        return "unreadable"
    return cell.text or "blank"


def _row_label(row: Row, index: int) -> str:
    return row.key or f"row {index + 1}"


def align_sheet(old: Sheet | None, new: Sheet, minter: IdMinter) -> tuple[Sheet, list[Change]]:
    changes: list[Change] = []
    old_cols = old.columns if old else []
    col_pairs = match(old_cols, new.columns, key=lambda c: _key(c.text), similar=lambda a, b: True)
    columns: list[Cell] = []
    for j, col in enumerate(new.columns):
        if j in col_pairs:
            prev = old_cols[col_pairs[j]]
            columns.append(col.model_copy(update={"id": prev.id}))
            if old is not None and prev.text != col.text:
                changes.append(
                    CellChanged(
                        prev.id,
                        "header",
                        prev.id,
                        "Header",
                        f"column {j + 1}",
                        _cell_label(prev),
                        _cell_label(col),
                        col.uncertain,
                        col.unreadable,
                        header=True,
                    )
                )
        else:
            columns.append(col.model_copy(update={"id": minter.mint("c")}))

    old_rows = old.rows if old else []
    old_col_index = {c.id: i for i, c in enumerate(old_cols)}

    def similar(a: Row, b: Row) -> bool:
        shared = [(old_col_index[c.id], j) for j, c in enumerate(columns) if c.id in old_col_index]
        if not shared:
            return False
        same = sum(
            1
            for i, j in shared
            if i < len(a.cells) and j < len(b.cells) and _key(a.cells[i].text) == _key(b.cells[j].text)
        )
        return same / len(shared) >= ROW_SIMILARITY

    row_pairs = match(
        old_rows, new.rows, key=lambda r: _key(r.key) or "|".join(_key(c.text) for c in r.cells), similar=similar
    )
    rows: list[Row] = []
    for j, row in enumerate(new.rows):
        prev_row = old_rows[row_pairs[j]] if j in row_pairs else None
        row_id = prev_row.id if prev_row else minter.mint("r")
        cells: list[Cell] = []
        for k, cell in enumerate(row.cells):
            col = columns[k]
            cells.append(cell.model_copy(update={"id": f"{row_id}.{col.id}"}))
            if prev_row is None or col.id not in old_col_index:
                continue
            i = old_col_index[col.id]
            if i >= len(prev_row.cells):
                continue
            before = prev_row.cells[i]
            if before.text != cell.text or before.unreadable != cell.unreadable:
                changes.append(
                    CellChanged(
                        f"{row_id}.{col.id}",
                        row_id,
                        col.id,
                        _row_label(row, j),
                        col.text or f"column {k + 1}",
                        _cell_label(before),
                        _cell_label(cell),
                        cell.uncertain,
                        cell.unreadable,
                    )
                )
        rows.append(Row(id=row_id, key=row.key, cells=cells))

    if old is not None:
        scroll = _scroll(len(old_rows), len(rows), row_pairs)
        if scroll and rows:
            direction, count = scroll
            changes.append(
                Scrolled(
                    "rows",
                    "down" if direction == "down" else "up",
                    _row_label(rows[0], 0),
                    _row_label(rows[-1], len(rows) - 1),
                    count,
                )
            )
        else:
            kept = set(row_pairs.values())
            removed = [r for i, r in enumerate(old_rows) if i not in kept]
            added = [(j, r) for j, r in enumerate(rows) if j not in row_pairs]
            if removed:
                changes.append(
                    RowsChanged(
                        "removed", tuple(r.id for r in removed), tuple(_row_label(r, i) for i, r in enumerate(removed))
                    )
                )
            if added:
                changes.append(
                    RowsChanged("added", tuple(r.id for _, r in added), tuple(_row_label(r, j) for j, r in added))
                )
    return Sheet(columns=columns, header_rows=new.header_rows, rows=rows, sheet_name=new.sheet_name), changes


def _line_label(line: CodeLine, index: int) -> str:
    return f"line {line.n if line.n is not None else index + 1}"


def align_code(old: Code | None, new: Code, minter: IdMinter) -> tuple[Code, list[Change]]:
    changes: list[Change] = []
    old_lines = old.lines if old else []
    pairs = match(old_lines, new.lines, key=lambda line: line.text.strip(), similar=lambda a, b: True)
    lines: list[CodeLine] = []
    for j, line in enumerate(new.lines):
        prev = old_lines[pairs[j]] if j in pairs else None
        lines.append(line.model_copy(update={"id": prev.id if prev else minter.mint("l")}))
        if prev is not None and (prev.text != line.text or prev.unreadable != line.unreadable):
            changes.append(
                LineChanged(prev.id, _line_label(line, j), prev.text, line.text, line.uncertain, line.unreadable)
            )
    if old is not None:
        scroll = _scroll(len(old_lines), len(lines), pairs) if len(pairs) > len(lines) // 2 else None
        if scroll and lines:
            direction, count = scroll
            changes.append(
                Scrolled(
                    "lines",
                    "down" if direction == "down" else "up",
                    _line_label(lines[0], 0),
                    _line_label(lines[-1], len(lines) - 1),
                    count,
                )
            )
        else:
            kept = set(pairs.values())
            removed = [(i, ln) for i, ln in enumerate(old_lines) if i not in kept]
            added = [(j, ln) for j, ln in enumerate(lines) if j not in pairs]
            if removed:
                changes.append(
                    LinesChanged(
                        "removed",
                        tuple(ln.id for _, ln in removed),
                        tuple(_line_label(ln, i) for i, ln in removed),
                        tuple(ln.text for _, ln in removed),
                    )
                )
            if added:
                changes.append(
                    LinesChanged(
                        "added",
                        tuple(ln.id for _, ln in added),
                        tuple(_line_label(ln, j) for j, ln in added),
                        tuple(ln.text for _, ln in added),
                    )
                )
    return Code(language=new.language, file_name=new.file_name, lines=lines), changes


def align_blocks(old: list[Block] | None, new: list[Block], minter: IdMinter) -> tuple[list[Block], list[Change]]:
    changes: list[Change] = []
    old_blocks = old or []
    pairs = match(old_blocks, new, key=lambda b: _key(b.text), similar=lambda a, b: a.kind == b.kind)
    blocks: list[Block] = []
    for j, block in enumerate(new):
        prev = old_blocks[pairs[j]] if j in pairs else None
        blocks.append(block.model_copy(update={"id": prev.id if prev else minter.mint("b")}))
        if prev is not None and prev.text != block.text:
            changes.append(BlockChanged(prev.id, block.kind, prev.text, block.text, block.uncertain))
    if old is not None:
        kept = set(pairs.values())
        removed = [b for i, b in enumerate(old_blocks) if i not in kept]
        added = [b for j, b in enumerate(blocks) if j not in pairs]
        if removed:
            changes.append(BlocksChanged("removed", tuple(b.id for b in removed), tuple(b.text for b in removed)))
        if added:
            changes.append(BlocksChanged("added", tuple(b.id for b in added), tuple(b.text for b in added)))
    return blocks, changes


def summarize(doc: Document) -> str:
    title = f", '{doc.title}'" if doc.title else ""
    if doc.content_type == "sheet" and doc.sheet:
        return f"Spreadsheet{title}, {len(doc.sheet.rows)} rows, {len(doc.sheet.columns)} columns"
    if doc.content_type == "code" and doc.code:
        name = doc.code.file_name or doc.title
        lang = f" {doc.code.language}" if doc.code.language else ""
        return f"Code{lang}{f', {name!r}' if name else ''}, {len(doc.code.lines)} lines".replace('"', "'")
    count = len(doc.blocks or [])
    kind = {"slide": "Slide", "doc": "Document"}.get(doc.content_type, "Unrecognised content")
    return f"{kind}{title}, {count} {'block' if count == 1 else 'blocks'}"


def align(old: Document | None, candidate: Document, minter: IdMinter) -> Alignment:
    version = old.version + 1 if old else 1
    switched = old is None or old.content_type != candidate.content_type
    base = None if switched else old
    changes: list[Change] = []
    update: dict[str, object] = {"version": version, "sheet": None, "code": None, "blocks": None}
    if candidate.sheet is not None:
        update["sheet"], changes = align_sheet(base.sheet if base else None, candidate.sheet, minter)
    elif candidate.code is not None:
        update["code"], changes = align_code(base.code if base else None, candidate.code, minter)
    else:
        update["blocks"], changes = align_blocks(base.blocks if base else None, candidate.blocks or [], minter)
    doc = candidate.model_copy(update=update)
    if switched:
        changes = [ContentTypeChanged(old.content_type if old else "none", doc.content_type, doc.title, summarize(doc))]
    elif old is not None and old.title != doc.title:
        changes.insert(0, TitleChanged(old.title, doc.title))
    return Alignment(doc=doc, changes=changes)
