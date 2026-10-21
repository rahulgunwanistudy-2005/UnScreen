"""Builders for documents and model reads used across tests."""

from engine.llm.schemas import (
    FullRead,
    ReadBlock,
    ReadCode,
    ReadColumn,
    ReadLine,
    ReadRow,
    ReadSheet,
)
from engine.model.document import Box, Cell, Code, CodeLine, Document, Row, Sheet

EMPTY_SHEET = ReadSheet(sheet_name="", columns=[], rows=[], unclear=[])
EMPTY_CODE = ReadCode(file_name="", language="", x_range=[0, 0], lines=[], unclear=[])


def box(x0: int = 0, y0: int = 0, x1: int = 10, y1: int = 10) -> Box:
    return Box(x0=x0, y0=y0, x1=x1, y1=y1)


def candidate_sheet(headers: list[str], rows: list[list[str]], title: str | None = "Q3 Pipeline") -> Document:
    """A candidate (no ids) laid out on a regular grid."""
    width = 1000 // max(1, len(headers))
    columns = [
        Cell(id="", text=h, bbox=box(j * width, 0, (j + 1) * width, 40), confidence=0.95) for j, h in enumerate(headers)
    ]
    out_rows = []
    for i, values in enumerate(rows):
        y0 = 40 + i * 40
        cells = [
            Cell(id="", text=v, bbox=box(j * width, y0, (j + 1) * width, y0 + 40), confidence=0.95)
            for j, v in enumerate(values)
        ]
        out_rows.append(Row(id="", key=values[0] or None, cells=cells))
    return Document(
        version=0,
        content_type="sheet",
        title=title,
        content_bbox=box(0, 0, 1000, 1000),
        sheet=Sheet(columns=columns, header_rows=1, rows=out_rows, sheet_name="Pipeline"),
    )


def candidate_code(lines: list[str], file_name: str = "app.py") -> Document:
    return Document(
        version=0,
        content_type="code",
        title=file_name,
        content_bbox=box(0, 0, 1000, 1000),
        code=Code(
            language="python",
            file_name=file_name,
            lines=[
                CodeLine(id="", n=i + 1, text=t, bbox=box(50, i * 20, 950, i * 20 + 20), confidence=0.95)
                for i, t in enumerate(lines)
            ],
        ),
    )


def full_sheet_read(headers: list[str], rows: list[list[str]], *, title: str = "Q3 Pipeline") -> FullRead:
    width = 1000 // max(1, len(headers))
    return FullRead(
        content_type="sheet",
        title=title,
        content_box_2d=[0, 0, 1000, 1000],
        sheet=ReadSheet(
            sheet_name="Pipeline",
            columns=[ReadColumn(header=h, x_range=[j * width, (j + 1) * width]) for j, h in enumerate(headers)],
            rows=[
                ReadRow(
                    y_range=[100 + i * 50, 150 + i * 50],
                    cells=list(values),
                )
                for i, values in enumerate(rows)
            ],
            unclear=[],
        ),
        code=EMPTY_CODE,
        blocks=[],
    )


def full_code_read(lines: list[str]) -> FullRead:
    return FullRead(
        content_type="code",
        title="app.py",
        content_box_2d=[0, 0, 1000, 1000],
        sheet=EMPTY_SHEET,
        code=ReadCode(
            file_name="app.py",
            language="python",
            x_range=[40, 900],
            lines=[ReadLine(n=i + 1, text=t, y_range=[i * 25, i * 25 + 25]) for i, t in enumerate(lines)],
            unclear=[],
        ),
        blocks=[],
    )


def full_slide_read(texts: list[str]) -> FullRead:
    return FullRead(
        content_type="slide",
        title=texts[0] if texts else "",
        content_box_2d=[0, 0, 1000, 1000],
        sheet=EMPTY_SHEET,
        code=EMPTY_CODE,
        blocks=[
            ReadBlock(
                kind="heading" if i == 0 else "list_item",
                level=1 if i == 0 else 0,
                text=t,
                legibility="clear",
                box_2d=[i * 100, 50, i * 100 + 80, 950],
            )
            for i, t in enumerate(texts)
        ],
    )
