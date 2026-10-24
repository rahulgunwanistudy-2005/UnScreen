"""Questions about the current frame, answered with citations that must exist in the document."""

import json
from dataclasses import dataclass
from typing import Any

from engine.model.document import Document
from engine.pipeline.frames import DecodedFrame
from engine.pipeline.reader import Reader


@dataclass(frozen=True)
class AskResult:
    text: str
    refs: list[str]
    rejected: list[str]
    latency_ms: int


def compact(doc: Document) -> dict[str, Any]:
    """The document without geometry, so the prompt stays small and ids stay visible."""
    out: dict[str, Any] = {"content_type": doc.content_type, "title": doc.title}

    def flag(unreadable: bool, uncertain: bool) -> dict[str, bool]:
        return {"unreadable": True} if unreadable else {"uncertain": True} if uncertain else {}

    if doc.sheet:
        out["columns"] = [{"id": c.id, "text": c.text, **flag(c.unreadable, c.uncertain)} for c in doc.sheet.columns]
        out["rows"] = [
            {"id": r.id, "cells": [{"id": c.id, "text": c.text, **flag(c.unreadable, c.uncertain)} for c in r.cells]}
            for r in doc.sheet.rows
        ]
    if doc.code:
        out["file_name"] = doc.code.file_name
        out["lines"] = [
            {"id": ln.id, "n": ln.n, "text": ln.text, **flag(ln.unreadable, ln.uncertain)} for ln in doc.code.lines
        ]
    if doc.blocks:
        out["blocks"] = [
            {"id": b.id, "kind": b.kind, "text": b.text, **flag(b.unreadable, b.uncertain)} for b in doc.blocks
        ]
    return out


def all_ids(doc: Document) -> set[str]:
    ids: set[str] = set()
    if doc.sheet:
        ids |= {c.id for c in doc.sheet.columns}
        ids |= {r.id for r in doc.sheet.rows} | {c.id for r in doc.sheet.rows for c in r.cells}
    if doc.code:
        ids |= {ln.id for ln in doc.code.lines}
    ids |= {b.id for b in doc.blocks or []}
    return ids


async def ask(reader: Reader, frame: DecodedFrame, doc: Document, question: str) -> AskResult:
    timed = await reader.ask(frame, json.dumps(compact(doc), ensure_ascii=False), question)
    known = all_ids(doc)
    refs = [r for r in dict.fromkeys(timed.value.refs) if r in known]
    rejected = [r for r in timed.value.refs if r not in known]
    text = timed.value.answer.strip() or "No answer."
    uncertain: set[str] = set()
    if doc.sheet:
        uncertain |= {c.id for c in doc.sheet.columns if c.uncertain or c.unreadable}
        for row in doc.sheet.rows:
            flagged = {c.id for c in row.cells if c.uncertain or c.unreadable}
            uncertain |= flagged
            if flagged:
                uncertain.add(row.id)
    if doc.code:
        uncertain |= {ln.id for ln in doc.code.lines if ln.uncertain or ln.unreadable}
    uncertain |= {b.id for b in doc.blocks or [] if b.uncertain or b.unreadable}
    if rejected or not refs:
        text = (
            "I could not verify this answer against readable references on screen. "
            "Please ask about a visible cell, line or block."
        )
        refs = []
    elif uncertain.intersection(refs):
        text = "The content needed for this answer is unclear or unreadable. I cannot state its value with confidence."
    return AskResult(text=text, refs=refs, rejected=rejected, latency_ms=timed.latency_ms)
