"""Tesseract baseline, standing in for screen-reader OCR (NVDA+R, JAWS OCR).

Screen-reader OCR reads out flat lines of text. To give the baseline every chance, we also
try to rebuild a grid from Tesseract's word boxes: words on one OCR line are split into
cells at large horizontal gaps, and the first line is taken as the header. That is more
structure than any screen reader's OCR offers, so the comparison favours the baseline."""

import csv
import io
import subprocess  # noqa: S404  # fixed argv, no shell
import tempfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from unscreen_bench.score import PredCell


@dataclass(frozen=True)
class Word:
    text: str
    left: int
    top: int
    width: int
    height: int
    line: tuple[int, int, int]
    conf: float


OCR_CONFIGS: list[tuple[int, int]] = [(3, 1), (6, 2), (11, 2)]
"""(page segmentation mode, upscale factor). The benchmark reports the best one over the set."""


def run_tesseract(image: Path, psm: int = 3, upscale: int = 1) -> list[Word]:
    source = image
    with tempfile.TemporaryDirectory() as tmp:
        if upscale != 1:
            with Image.open(image) as img:
                source = Path(tmp) / "up.png"
                img.resize((img.width * upscale, img.height * upscale), Image.Resampling.LANCZOS).save(source)
        out = subprocess.run(  # noqa: S603
            ["tesseract", str(source), "stdout", "--psm", str(psm), "tsv"],  # noqa: S607
            capture_output=True,
            check=True,
            text=True,
        ).stdout
    words: list[Word] = []
    for row in csv.DictReader(io.StringIO(out), delimiter="\t", quoting=csv.QUOTE_NONE):
        text = (row.get("text") or "").strip()
        if row.get("level") != "5" or not text:
            continue
        words.append(
            Word(
                text=text,
                left=int(row["left"]) // upscale,
                top=int(row["top"]) // upscale,
                width=int(row["width"]) // upscale,
                height=int(row["height"]) // upscale,
                line=(int(row["block_num"]), int(row["par_num"]), int(row["line_num"])),
                conf=float(row["conf"]),
            )
        )
    return words


def lines(words: list[Word]) -> list[list[Word]]:
    grouped: dict[tuple[int, int, int], list[Word]] = {}
    for w in words:
        grouped.setdefault(w.line, []).append(w)
    out = [sorted(ws, key=lambda w: w.left) for ws in grouped.values()]
    out.sort(key=lambda ws: (min(w.top for w in ws), ws[0].left))
    return out


def flat_text(words: list[Word]) -> list[str]:
    """What a screen reader's OCR would read: one string per line."""
    return [" ".join(w.text for w in ln) for ln in lines(words)]


def grid(words: list[Word]) -> list[list[PredCell]]:
    """Best-effort table: split each line at gaps wider than 1.2x the line's text height."""
    rows: list[list[PredCell]] = []
    for ln in lines(words):
        cells: list[list[Word]] = [[ln[0]]]
        for prev, w in zip(ln, ln[1:], strict=False):
            gap = w.left - (prev.left + prev.width)
            if gap > 1.2 * max(prev.height, w.height):
                cells.append([w])
            else:
                cells[-1].append(w)
        rows.append([PredCell(text=" ".join(x.text for x in c), confident=True, flagged=False) for c in cells])
    return rows
