"""What the vision model returns. Deliberately separate from the Document model: the model
never mints ids, every coordinate is relative to the image it was shown, and nothing is
nullable (empty strings and empty lists instead) so the response schema stays small."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Legibility = Literal["clear", "unsure", "unreadable"]
ReadContentType = Literal["sheet", "code", "slide", "doc", "unknown"]
ReadBlockKind = Literal["heading", "paragraph", "list_item", "figure", "table_ref"]

Range = list[int]
Box2d = list[int]


class _Read(BaseModel):
    model_config = ConfigDict(extra="ignore")


class ReadCell(_Read):
    """Internal pairing of a transcription and its legibility; not sent as a schema."""

    text: str
    legibility: Legibility


class Unclear(_Read):
    row: int = Field(description="Row index in rows (-1 for the header row), or line index in lines.")
    col: int = Field(description="Column index; 0 for code lines.")
    legibility: Literal["unsure", "unreadable"]


class ReadColumn(_Read):
    header: str = Field(description="Header cell text exactly as shown.")
    x_range: Range = Field(min_length=2, max_length=2, description="[x_min, x_max], 0-1000")


class ReadRow(_Read):
    y_range: Range = Field(min_length=2, max_length=2, description="[y_min, y_max], 0-1000")
    cells: list[str] = Field(description="One string per column, in column order, exactly as shown.")


class ReadSheet(_Read):
    sheet_name: str = Field(description="Name of the active sheet tab, or empty.")
    columns: list[ReadColumn]
    rows: list[ReadRow]
    unclear: list[Unclear] = Field(description="Only cells that are not perfectly legible. Usually empty.")


class ReadLine(_Read):
    n: int = Field(description="Line number shown in the gutter, or 0 if none is shown.")
    text: str = Field(description="The line's code exactly, including leading spaces.")
    y_range: Range = Field(min_length=2, max_length=2)


class ReadCode(_Read):
    file_name: str = Field(description="File name shown in the editor tab, or empty.")
    language: str = Field(description="Programming language if obvious from the file name, or empty.")
    x_range: Range = Field(min_length=2, max_length=2, description="Horizontal extent of the code text.")
    lines: list[ReadLine]
    unclear: list[Unclear] = Field(description="Only lines that are not perfectly legible. Usually empty.")


class ReadBlock(_Read):
    kind: ReadBlockKind
    level: int = Field(description="Heading level 1-6 for headings, otherwise 0.")
    text: str
    legibility: Legibility
    box_2d: Box2d = Field(min_length=4, max_length=4, description="[ymin, xmin, ymax, xmax], 0-1000")


class FullRead(_Read):
    content_type: ReadContentType
    title: str = Field(description="Document, file or slide title if visible, or empty.")
    content_box_2d: Box2d = Field(
        min_length=4,
        max_length=4,
        description="[ymin, xmin, ymax, xmax] of the shared content, excluding meeting-app chrome.",
    )
    sheet: ReadSheet
    code: ReadCode
    blocks: list[ReadBlock]


class RegionRow(_Read):
    cells: list[str]


class SheetRegionRead(_Read):
    rows: list[RegionRow]
    unclear: list[Unclear] = Field(description="Only cells that are not perfectly legible. Usually empty.")


class CodeRegionRead(_Read):
    lines: list[ReadLine]
    unclear: list[Unclear] = Field(description="Only lines that are not perfectly legible. Usually empty.")


def legibility_of(unclear: list[Unclear]) -> dict[tuple[int, int], Legibility]:
    return {(u.row, u.col): u.legibility for u in unclear}


class Reading(_Read):
    text: str
    legibility: Legibility


class VerifyRead(_Read):
    readings: list[Reading]


class AskAnswer(_Read):
    answer: str = Field(description="Short answer in plain language.")
    refs: list[str] = Field(description="Ids of the cells, lines or blocks the answer relies on.")


def response_schema(model: type[BaseModel]) -> dict[str, Any]:
    """JSON Schema for the model's structured output, with $refs inlined and titles dropped."""
    raw = model.model_json_schema()
    defs: dict[str, Any] = raw.pop("$defs", {})

    def resolve(node: Any) -> Any:
        if isinstance(node, dict):
            if "$ref" in node:
                return resolve(defs[node["$ref"].split("/")[-1]])
            out: dict[str, Any] = {}
            for k, v in node.items():
                if k == "properties":
                    out[k] = {name: resolve(prop) for name, prop in v.items()}
                elif k not in ("title", "default"):
                    out[k] = resolve(v)
            return out
        if isinstance(node, list):
            return [resolve(v) for v in node]
        return node

    schema: dict[str, Any] = resolve(raw)
    return schema
