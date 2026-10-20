"""The document model: the single source of truth for what UnScreen shows and says.

Every coordinate is normalised to 0..1000 of the full captured frame. Ids are minted by the
aligner, never by the model, and are preserved across versions.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ContentType = Literal["sheet", "code", "slide", "doc", "unknown"]
BlockKind = Literal["heading", "paragraph", "list_item", "figure", "table_ref"]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_serialization_defaults_required=True)


class Box(_Strict):
    """Axis-aligned box, normalised 0..1000 (x grows right, y grows down)."""

    x0: int = Field(ge=0, le=1000)
    y0: int = Field(ge=0, le=1000)
    x1: int = Field(ge=0, le=1000)
    y1: int = Field(ge=0, le=1000)


FULL_FRAME = Box(x0=0, y0=0, x1=1000, y1=1000)


class Cell(_Strict):
    id: str
    text: str
    bbox: Box
    confidence: float = Field(ge=0.0, le=1.0)
    unreadable: bool = False
    uncertain: bool = False


class Row(_Strict):
    id: str
    key: str | None
    cells: list[Cell]


class Sheet(_Strict):
    columns: list[Cell]
    header_rows: int = Field(ge=0)
    rows: list[Row]
    sheet_name: str | None = None


class CodeLine(_Strict):
    id: str
    n: int | None
    text: str
    bbox: Box
    confidence: float = Field(ge=0.0, le=1.0)
    unreadable: bool = False
    uncertain: bool = False


class Code(_Strict):
    language: str | None = None
    file_name: str | None = None
    lines: list[CodeLine]


class Block(_Strict):
    id: str
    kind: BlockKind
    level: int | None = None
    text: str
    bbox: Box
    confidence: float = Field(ge=0.0, le=1.0)
    unreadable: bool = False
    uncertain: bool = False


class Document(_Strict):
    version: int = Field(ge=0)
    content_type: ContentType
    title: str | None = None
    content_bbox: Box
    sheet: Sheet | None = None
    code: Code | None = None
    blocks: list[Block] | None = None


def empty_document() -> Document:
    return Document(version=0, content_type="unknown", title=None, content_bbox=FULL_FRAME)
