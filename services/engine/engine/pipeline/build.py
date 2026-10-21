"""Turn model reads into candidate Documents. Candidates have empty ids; the aligner assigns them."""

from engine.llm.schemas import FullRead, Legibility, ReadCell, ReadCode, ReadLine, ReadSheet, legibility_of
from engine.model.document import Block, Box, Cell, Code, CodeLine, Document, Row, Sheet
from engine.pipeline.geometry import from_box_2d, make_box, map_x, map_y

CONFIDENCE: dict[Legibility, float] = {"clear": 0.95, "unsure": 0.5, "unreadable": 0.0}


def norm_text(text: str) -> str:
    return " ".join(text.replace(" ", " ").split())


def flags(legibility: Legibility) -> tuple[float, bool, bool]:
    return CONFIDENCE[legibility], legibility == "unreadable", legibility == "unsure"


def cell_from(read: ReadCell, bbox: Box) -> Cell:
    conf, unreadable, uncertain = flags(read.legibility)
    return Cell(
        id="",
        text="" if unreadable else norm_text(read.text),
        bbox=bbox,
        confidence=conf,
        unreadable=unreadable,
        uncertain=uncertain,
    )


def _span(r: list[int], within: Box, axis: str) -> tuple[float, float]:
    lo, hi = (r[0], r[1]) if len(r) == 2 else (0, 1000)
    f = map_x if axis == "x" else map_y
    return f(min(lo, hi), within), f(max(lo, hi), within)


def build_sheet(read: ReadSheet, within: Box) -> Sheet | None:
    if not read.columns:
        return None
    xs = [_span(c.x_range, within, "x") for c in read.columns]
    header_y: tuple[float, float] = (within.y0, within.y0)
    if read.rows:
        first = _span(read.rows[0].y_range, within, "y")
        height = max(8.0, first[1] - first[0])
        header_y = (max(within.y0, first[0] - height), first[0])
    leg = legibility_of(read.unclear)
    columns = [
        cell_from(
            ReadCell(text=c.header, legibility=leg.get((-1, j), "clear")), make_box(x0, header_y[0], x1, header_y[1])
        )
        for j, (c, (x0, x1)) in enumerate(zip(read.columns, xs, strict=True))
    ]
    rows: list[Row] = []
    for i, r in enumerate(read.rows):
        y0, y1 = _span(r.y_range, within, "y")
        values = list(r.cells[: len(columns)])
        values += [""] * (len(columns) - len(values))
        cells = [
            cell_from(ReadCell(text=v, legibility=leg.get((i, j), "clear")), make_box(x0, y0, x1, y1))
            for j, (v, (x0, x1)) in enumerate(zip(values, xs, strict=True))
        ]
        key = cells[0].text if cells and not cells[0].unreadable and cells[0].text else None
        rows.append(Row(id="", key=key, cells=cells))
    return Sheet(columns=columns, header_rows=1, rows=rows, sheet_name=norm_text(read.sheet_name) or None)


def line_from(read: ReadLine, x: tuple[float, float], within: Box, legibility: Legibility = "clear") -> CodeLine:
    conf, unreadable, uncertain = flags(legibility)
    y0, y1 = _span(read.y_range, within, "y")
    return CodeLine(
        id="",
        n=read.n if read.n > 0 else None,
        text="" if unreadable else read.text.replace("\t", "    ").rstrip(),
        bbox=make_box(x[0], y0, x[1], y1),
        confidence=conf,
        unreadable=unreadable,
        uncertain=uncertain,
    )


def build_code(read: ReadCode, within: Box) -> Code | None:
    if not read.lines:
        return None
    x = _span(read.x_range, within, "x")
    if x[1] - x[0] < 5:
        x = (within.x0, within.x1)
    return Code(
        language=norm_text(read.language) or None,
        file_name=norm_text(read.file_name) or None,
        lines=[
            line_from(line, x, within, legibility_of(read.unclear).get((i, 0), "clear"))
            for i, line in enumerate(read.lines)
        ],
    )


def build_document(read: FullRead, within: Box) -> Document:
    """`within` is the frame box of the image the model saw."""
    content_bbox = from_box_2d(read.content_box_2d, within)
    if content_bbox.x1 - content_bbox.x0 < 50 or content_bbox.y1 - content_bbox.y0 < 50:
        content_bbox = within
    title = norm_text(read.title) or None
    if read.content_type == "sheet":
        sheet = build_sheet(read.sheet, within)
        if sheet is not None:
            return Document(version=0, content_type="sheet", title=title, content_bbox=content_bbox, sheet=sheet)
    if read.content_type == "code":
        code = build_code(read.code, within)
        if code is not None:
            return Document(version=0, content_type="code", title=title, content_bbox=content_bbox, code=code)
    blocks: list[Block] = []
    for b in read.blocks:
        conf, unreadable, uncertain = flags(b.legibility)
        blocks.append(
            Block(
                id="",
                kind=b.kind,
                level=b.level if b.kind == "heading" and 1 <= b.level <= 6 else None,
                text="" if unreadable else norm_text(b.text),
                bbox=from_box_2d(b.box_2d, within),
                confidence=conf,
                unreadable=unreadable,
                uncertain=uncertain,
            )
        )
    content_type = read.content_type if read.content_type in ("slide", "doc") else "unknown"
    return Document(version=0, content_type=content_type, title=title, content_bbox=content_bbox, blocks=blocks)
