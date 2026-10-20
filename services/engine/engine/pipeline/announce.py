"""Render semantic changes as short spoken sentences. Uncertain values are never spoken as fact."""

from engine.model.protocol import Announce, AnnounceKind, NumericStyle, Priority
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

MAX_PER_KIND = 5
MAX_SPOKEN_LINE = 120


def _clip(text: str) -> str:
    text = text.strip() or "blank line"
    return text if len(text) <= MAX_SPOKEN_LINE else text[: MAX_SPOKEN_LINE - 1] + "…"


def _list(labels: tuple[str, ...], limit: int = 3) -> str:
    shown = list(labels[:limit])
    rest = len(labels) - len(shown)
    if rest > 0:
        return ", ".join(shown) + f" and {rest} more"
    if len(shown) > 1:
        return ", ".join(shown[:-1]) + " and " + shown[-1]
    return shown[0] if shown else ""


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def render(change: Change, style: NumericStyle) -> tuple[AnnounceKind, str, list[str]]:
    """-> (kind, text, refs)"""
    match change:
        case ContentTypeChanged(summary=summary):
            return "content_type", f"Now showing: {summary}.", []
        case TitleChanged(new=new):
            return "title", f"Title changed to {new}." if new else "Title removed.", []
        case CellChanged() if change.unreadable or change.uncertain:
            where = f"{change.row_label}, {change.col_label}"
            if change.unreadable:
                return "uncertain", f"{where}: changed, now unreadable.", [change.cell_id]
            return "uncertain", f"{where}: possibly changed, unclear.", [change.cell_id]
        case CellChanged(header=True):
            return "cell", f"Column header changed: {change.old} to {change.new}.", [change.cell_id]
        case CellChanged():
            where = f"{change.row_label}, {change.col_label}"
            if style == "new_only":
                return "cell", f"{where}: {change.new}.", [change.cell_id]
            return "cell", f"{where}: {change.old} to {change.new}.", [change.cell_id]
        case RowsChanged(kind=kind, row_ids=ids, labels=labels):
            n = len(ids)
            head = f"Row {kind}" if n == 1 else f"{n} rows {kind}"
            return ("row_added" if kind == "added" else "row_removed"), f"{head}: {_list(labels)}.", list(ids)
        case Scrolled(unit=unit, direction=direction, count=count, first_label=first, last_label=last):
            noun = {"rows": "row", "lines": "line", "blocks": "block"}[unit]
            return "scroll", f"Scrolled {direction} {_plural(count, noun)}. Now showing {first} to {last}.", []
        case LineChanged() if change.unreadable or change.uncertain:
            state = "now unreadable" if change.unreadable else "possibly changed, unclear"
            return "uncertain", f"{change.label.capitalize()}: {state}.", [change.line_id]
        case LineChanged():
            if style == "new_only":
                return "line", f"{change.label.capitalize()} now reads: {_clip(change.new)}", [change.line_id]
            return (
                "line",
                f"{change.label.capitalize()} changed. Was: {_clip(change.old)}. Now: {_clip(change.new)}",
                [change.line_id],
            )
        case LinesChanged(kind=kind, line_ids=ids, labels=labels, texts=texts):
            akind: AnnounceKind = "lines_added" if kind == "added" else "lines_removed"
            if len(ids) == 1:
                return akind, f"{labels[0].capitalize()} {kind}: {_clip(texts[0])}", list(ids)
            return akind, f"{len(ids)} lines {kind}, {labels[0]} to {labels[-1]}.", list(ids)
        case BlockChanged(uncertain=True):
            return "uncertain", "A block possibly changed, unclear.", [change.block_id]
        case BlockChanged(new=new, block_id=bid):
            return "block", f"Changed: {_clip(new)}", [bid]
        case BlocksChanged(kind=kind, block_ids=ids, texts=texts):
            if len(ids) == 1:
                return "block", f"{kind.capitalize()}: {_clip(texts[0])}", list(ids)
            return "block", f"{len(ids)} blocks {kind}.", list(ids)
    raise AssertionError(f"unhandled change {change!r}")


def _priority(kind: str, refs: list[str], focus_ref: str | None) -> Priority:
    if kind == "content_type":
        return "content_type"
    if focus_ref and any(r == focus_ref or r.startswith(focus_ref + ".") or r.endswith("." + focus_ref) for r in refs):
        return "focus"
    return "other"


def announcements(changes: list[Change], version: int, style: NumericStyle, focus_ref: str | None) -> list[Announce]:
    rendered = [render(c, style) for c in changes]
    out: list[Announce] = []
    by_kind: dict[AnnounceKind, list[tuple[str, list[str]]]] = {}
    for kind, text, refs in rendered:
        by_kind.setdefault(kind, []).append((text, refs))
    for kind, items in by_kind.items():
        focused = [(t, r) for t, r in items if _priority(kind, r, focus_ref) == "focus"]
        rest = [(t, r) for t, r in items if (t, r) not in focused]
        for text, refs in focused:
            out.append(Announce(version=version, priority="focus", kind=kind, text=text, refs=refs))
        if len(rest) > MAX_PER_KIND and kind in ("cell", "line", "uncertain"):
            refs = [r for _, rs in rest for r in rs]
            noun = "cells" if kind == "cell" else "lines" if kind == "line" else "values"
            text = (
                f"{len(rest)} {noun} changed."
                if kind != "uncertain"
                else f"{len(rest)} values possibly changed, unclear."
            )
            out.append(Announce(version=version, priority="other", kind=kind, text=text, refs=refs))
            continue
        for text, refs in rest:
            out.append(
                Announce(version=version, priority=_priority(kind, refs, focus_ref), kind=kind, text=text, refs=refs)
            )
    order = {"content_type": 0, "focus": 1, "other": 2}
    out.sort(key=lambda a: order[a.priority])
    return out
