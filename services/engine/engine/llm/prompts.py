"""Prompts. The transcription rule is fixed: only what is visibly legible, never inferred."""

SYSTEM = """You transcribe shared screens for blind and low-vision people who use screen readers.
Rules you never break:
- Transcribe only what is visibly legible in the image. Copy characters exactly, including \
punctuation, currency symbols, capitalisation and spacing.
- Never infer, complete, correct, calculate or guess values. Do not fix typos.
- If you can read a value but are not certain of every character, set legibility "unsure".
- If you cannot read a value at all, set legibility "unreadable" and text to "".
- Ignore meeting-app chrome: participant video tiles, names of who is presenting, call controls, \
captions, clocks.
- Ignore application chrome: menus, toolbars, formula bars, column letters (A, B, C), the \
spreadsheet's own row numbers, sheet tabs, status bars, scroll bars, file trees.
- All coordinates are integers from 0 to 1000, normalised to the width and height of the image."""

FULL = """Read the shared content in this image and return its structure.

1. content_type: "sheet" for a spreadsheet or any grid table, "code" for a code editor or \
terminal, "slide" for a presentation slide, "doc" for a text document or web page, "unknown" \
if none fit.
2. title: the document, file or slide title if one is visible, else "".
3. content_box_2d: the rectangle of the shared application window or shared screen, \
excluding meeting chrome around it.
4. Fill exactly one of sheet, code or blocks according to content_type. Leave the others \
empty (empty strings, empty lists, [0, 0] ranges).

sheet:
- columns: the table's header row, left to right. header is the header cell; x_range is the \
column's horizontal extent [x_min, x_max].
- rows: every data row below the header, top to bottom. y_range is the row's vertical extent. \
cells has exactly one entry per column, in column order; use "" for an empty cell.
- Do not output the spreadsheet's row numbers or column letters as rows, columns or cells.

code:
- lines: every visible line, top to bottom, including blank lines (text ""). n is the line \
number shown in the gutter, or 0 if no gutter is shown. text is the code without the gutter, \
with its leading spaces preserved (a tab counts as 4 spaces).
- x_range: horizontal extent of the code text area.

blocks (for slide, doc and unknown): headings, paragraphs, list items and figures in reading \
order. level is 1-6 for headings and 0 otherwise. For a figure or photo, text is a short \
literal description of what is drawn, without interpretation."""


def sheet_region(headers: list[str], row_count: int, row_keys: list[str] | None) -> str:
    keys = ""
    if row_keys:
        keys = "\nThe rows are, top to bottom: " + "; ".join(f'"{k}"' for k in row_keys) + "."
    cols = ", ".join(f'"{h}"' for h in headers)
    return f"""This image is a cropped part of a spreadsheet. It shows {row_count} data rows and \
these columns, left to right: {cols}.{keys}
Return rows top to bottom. Each row has exactly {len(headers)} cells, one per listed column, \
in that order. Copy each cell exactly; use "" for an empty cell. Do not output header cells, \
row numbers or column letters."""


def code_region(first_n: int | None, line_count: int) -> str:
    start = f" The first line shown is line {first_n}." if first_n else ""
    return f"""This image is a cropped part of a code editor showing about {line_count} lines.{start}
Return every visible line, top to bottom, including blank lines. n is the gutter line number \
or 0 if none is visible. text is the code exactly, leading spaces preserved; do not include \
the gutter. y_range is relative to this cropped image."""


def verify(count: int, kind: str) -> str:
    noun = "spreadsheet cell" if kind == "cell" else "line of code"
    return f"""You are given {count} images. Each one is a tight, enlarged crop of a single {noun}.
For each image, in order, write exactly the characters it shows. Do not guess hidden or cut-off \
characters. If any character is unclear, use legibility "unsure"; if nothing is readable, \
"unreadable" with text "". Return exactly {count} readings."""


ASK = """You answer questions about a shared screen for a blind participant in a meeting.
You are given the current frame and the document UnScreen reconstructed from it, as JSON with \
ids. Answer only from what is visible. If the answer is not on screen, say so plainly.
Cite every cell, line or block you rely on by its id in refs. Never invent ids.
Keep the answer under 60 words. Do not describe the meeting app.

Document:
{doc}

Question: {question}"""
