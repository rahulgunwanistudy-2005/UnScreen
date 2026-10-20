"""Score a reconstructed Document against fixture ground truth. Pure functions, no I/O."""

from dataclasses import asdict, dataclass, field
from difflib import SequenceMatcher
from typing import Any

from engine.model.document import Document


def norm(s: str) -> str:
    return " ".join(s.replace(" ", " ").split())


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


@dataclass
class Score:
    kind: str
    truth_items: int = 0
    exact: int = 0
    char_errors: int = 0
    truth_chars: int = 0
    predicted_confident: int = 0
    hallucinated: int = 0
    found_anywhere: int = 0
    placed_correctly: int = 0
    flagged: int = 0
    flagged_wrong: int = 0
    content_type_ok: bool = False
    notes: list[str] = field(default_factory=list)

    @property
    def exact_rate(self) -> float:
        return self.exact / self.truth_items if self.truth_items else 0.0

    @property
    def cer(self) -> float:
        return self.char_errors / self.truth_chars if self.truth_chars else 0.0

    @property
    def hallucination_rate(self) -> float:
        return self.hallucinated / self.predicted_confident if self.predicted_confident else 0.0

    @property
    def structure_rate(self) -> float:
        return self.placed_correctly / self.found_anywhere if self.found_anywhere else 0.0

    def to_json(self) -> dict[str, Any]:
        d = asdict(self)
        d.update(
            exact_rate=self.exact_rate,
            cer=self.cer,
            hallucination_rate=self.hallucination_rate,
            structure_rate=self.structure_rate,
        )
        return d


@dataclass(frozen=True)
class PredCell:
    text: str
    confident: bool
    flagged: bool


Grid = list[list[PredCell]]


def _align(truth_keys: list[str], pred_keys: list[str]) -> dict[int, int]:
    """truth index -> pred index, by exact key runs then position inside replaced runs."""
    m = SequenceMatcher(a=truth_keys, b=pred_keys, autojunk=False)
    pairs: dict[int, int] = {}
    for tag, i1, i2, j1, j2 in m.get_opcodes():
        if tag in ("equal", "replace"):
            for k in range(min(i2 - i1, j2 - j1)):
                pairs[i1 + k] = j1 + k
    return pairs


def score_grid(
    truth_headers: list[str], truth_rows: list[list[str]], pred_headers: list[PredCell], pred_rows: Grid, kind: str = "sheet"
) -> Score:
    s = Score(kind=kind)
    th = [norm(h) for h in truth_headers]
    ph = [norm(h.text) for h in pred_headers]
    col_pairs = _align([h.lower() for h in th], [h.lower() for h in ph])
    row_pairs = _align(
        [norm(r[0]).lower() if r else "" for r in truth_rows],
        [norm(r[0].text).lower() if r else "" for r in pred_rows],
    )
    truth_grid = [th, *[[norm(v) for v in r] for r in truth_rows]]
    pred_grid: Grid = [pred_headers, *pred_rows]
    rp = {0: 0, **{i + 1: j + 1 for i, j in row_pairs.items()}}
    used: set[tuple[int, int]] = set()
    pred_texts: dict[str, int] = {}
    for r in pred_grid:
        for c in r:
            if c.text:
                pred_texts[norm(c.text)] = pred_texts.get(norm(c.text), 0) + 1
    for i, row in enumerate(truth_grid):
        for j, truth in enumerate(row):
            s.truth_items += 1
            s.truth_chars += len(truth)
            if truth and norm(truth) in pred_texts:
                s.found_anywhere += 1
            pi, pj = rp.get(i), col_pairs.get(j)
            cell = None
            if pi is not None and pj is not None and pi < len(pred_grid) and pj < len(pred_grid[pi]):
                cell = pred_grid[pi][pj]
                used.add((pi, pj))
            got = norm(cell.text) if cell else ""
            s.char_errors += levenshtein(got, truth)
            if cell is not None and got == truth:
                s.exact += 1
                if truth:
                    s.placed_correctly += 1
            if cell is not None and cell.flagged:
                s.flagged += 1
                if got != truth:
                    s.flagged_wrong += 1
            if cell is not None and cell.confident:
                s.predicted_confident += 1
                if got != truth:
                    s.hallucinated += 1
    for pi, r in enumerate(pred_grid):
        for pj, c in enumerate(r):
            if (pi, pj) not in used and c.confident and c.text:
                s.predicted_confident += 1
                s.hallucinated += 1
    return s


def _cell(text: str, unreadable: bool, uncertain: bool) -> PredCell:
    return PredCell(text="" if unreadable else text, confident=not (unreadable or uncertain), flagged=unreadable or uncertain)


def score_document(truth: dict[str, Any], doc: Document | None) -> Score:
    kind = truth["content_type"]
    if kind == "sheet":
        t = truth["sheet"]
        if doc is None or doc.sheet is None:
            s = score_grid(t["columns"], t["rows"], [], [], "sheet")
        else:
            headers = [_cell(c.text, c.unreadable, c.uncertain) for c in doc.sheet.columns]
            rows = [[_cell(c.text, c.unreadable, c.uncertain) for c in r.cells] for r in doc.sheet.rows]
            s = score_grid(t["columns"], t["rows"], headers, rows, "sheet")
    elif kind == "code":
        lines = [ln["text"].rstrip() for ln in truth["code"]["lines"]]
        pred = [] if doc is None or doc.code is None else [_cell(ln.text.rstrip(), ln.unreadable, ln.uncertain) for ln in doc.code.lines]
        s = score_lines(lines, pred)
    else:
        blocks = [b["text"] for b in truth["blocks"]]
        pred = [] if doc is None or not doc.blocks else [_cell(b.text, b.unreadable, b.uncertain) for b in doc.blocks]
        s = score_lines(blocks, pred, kind="blocks", exact_whitespace=False)
    s.content_type_ok = doc is not None and (doc.content_type == kind or (kind in ("slide", "doc") and doc.content_type in ("slide", "doc")))
    return s


def score_lines(truth: list[str], pred: list[PredCell], kind: str = "code", exact_whitespace: bool = True) -> Score:
    """Lines (code) or blocks: aligned by sequence; code keeps leading whitespace exact."""
    s = Score(kind=kind)
    def key(t: str) -> str:
        return t.rstrip() if exact_whitespace else norm(t)
    tk = [key(t) for t in truth]
    pk = [key(p.text) for p in pred]
    pairs = _align(tk, pk)
    used = set(pairs.values())
    present = set(pk)
    for i, t in enumerate(tk):
        s.truth_items += 1
        s.truth_chars += len(t)
        if t in present and t:
            s.found_anywhere += 1
        j = pairs.get(i)
        got = pk[j] if j is not None else ""
        s.char_errors += levenshtein(got, t)
        if j is not None and got == t:
            s.exact += 1
            if t:
                s.placed_correctly += 1
        if j is not None and pred[j].flagged:
            s.flagged += 1
            if got != t:
                s.flagged_wrong += 1
        if j is not None and pred[j].confident:
            s.predicted_confident += 1
            if got != t:
                s.hallucinated += 1
    for j, p in enumerate(pred):
        if j not in used and p.confident and p.text.strip():
            s.predicted_confident += 1
            s.hallucinated += 1
    return s
