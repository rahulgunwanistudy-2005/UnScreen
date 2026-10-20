"""Semantic changes between two document versions. Announcements are rendered from these."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ContentTypeChanged:
    old: str
    new: str
    title: str | None
    summary: str


@dataclass(frozen=True)
class TitleChanged:
    old: str | None
    new: str | None


@dataclass(frozen=True)
class CellChanged:
    cell_id: str
    row_id: str
    col_id: str
    row_label: str
    col_label: str
    old: str
    new: str
    uncertain: bool
    unreadable: bool
    header: bool = False


@dataclass(frozen=True)
class RowsChanged:
    kind: Literal["added", "removed"]
    row_ids: tuple[str, ...]
    labels: tuple[str, ...]


@dataclass(frozen=True)
class Scrolled:
    unit: Literal["rows", "lines", "blocks"]
    direction: Literal["up", "down"]
    first_label: str
    last_label: str
    count: int


@dataclass(frozen=True)
class LineChanged:
    line_id: str
    label: str
    old: str
    new: str
    uncertain: bool
    unreadable: bool


@dataclass(frozen=True)
class LinesChanged:
    kind: Literal["added", "removed"]
    line_ids: tuple[str, ...]
    labels: tuple[str, ...]
    texts: tuple[str, ...]


@dataclass(frozen=True)
class BlockChanged:
    block_id: str
    kind: str
    old: str
    new: str
    uncertain: bool


@dataclass(frozen=True)
class BlocksChanged:
    kind: Literal["added", "removed"]
    block_ids: tuple[str, ...]
    texts: tuple[str, ...]


Change = (
    ContentTypeChanged
    | TitleChanged
    | CellChanged
    | RowsChanged
    | Scrolled
    | LineChanged
    | LinesChanged
    | BlockChanged
    | BlocksChanged
)
