"""One session's reconstruction loop: decide full vs region read, verify, align, diff, announce."""

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass, field, replace
from typing import Literal

from engine.config import Settings
from engine.llm.client import ModelError, VisionModel
from engine.llm.cost import CostMeter
from engine.llm.schemas import ReadCell, Reading, legibility_of
from engine.model.document import FULL_FRAME, Box, Cell, CodeLine, Document
from engine.model.protocol import Announce, NumericStyle, PatchOp
from engine.pipeline import align as aligner
from engine.pipeline.announce import announcements
from engine.pipeline.build import build_document, cell_from, flags, norm_text
from engine.pipeline.changes import CellChanged, Change, LineChanged
from engine.pipeline.crosscheck import cross_check
from engine.pipeline.diff import diff
from engine.pipeline.frames import DecodedFrame, compare, decode, same_frame
from engine.pipeline.geometry import area, pad, union
from engine.pipeline.pointer import describe_pointer
from engine.pipeline.reader import Reader

log = logging.getLogger(__name__)

Mode = Literal["unchanged", "ignored", "cache", "full", "region"]
CACHE_SIZE = 6
TIGHTEN_RATIO = 0.7


@dataclass
class Outcome:
    mode: Mode
    doc: Document | None
    base: int
    ops: list[PatchOp] = field(default_factory=list)
    announces: list[Announce] = field(default_factory=list)
    model_ms: int = 0
    total_ms: int = 0

    @property
    def changed(self) -> bool:
        return bool(self.announces)


class RegionMismatchError(Exception):
    """The region read did not line up with the known structure; fall back to a full read."""


def _agree(a: str, b: str) -> bool:
    def squash(s: str) -> str:
        return norm_text(s).replace(" ", "").lower()

    return squash(a) == squash(b)


def _merge_reading(primary: ReadCell, check: Reading) -> ReadCell:
    """Two independent reads of the same cell. Disagreement makes it uncertain, never a value."""
    if primary.legibility == "unreadable" and check.legibility == "unreadable":
        return primary
    if primary.legibility == "unreadable" or check.legibility == "unreadable":
        return ReadCell(text=primary.text or check.text, legibility="unsure")
    if not _agree(primary.text, check.text):
        return ReadCell(text=primary.text, legibility="unsure")
    worst = "unsure" if "unsure" in (primary.legibility, check.legibility) else "clear"
    return ReadCell(text=primary.text, legibility=worst)


class SessionPipeline:
    def __init__(self, model: VisionModel, settings: Settings) -> None:
        self.settings = settings
        self.meter = CostMeter()
        self.reader = Reader(model, settings, self.meter)
        self.minter = aligner.IdMinter()
        self.doc: Document | None = None
        self.frame: DecodedFrame | None = None
        self.cache: deque[tuple[DecodedFrame, Document]] = deque(maxlen=CACHE_SIZE)
        self.numeric_style: NumericStyle = "old_to_new"
        self.focus_ref: str | None = None
        self.lock = asyncio.Lock()

    async def process(self, data: bytes) -> Outcome:
        async with self.lock:
            return await self._process(data)

    async def _process(self, data: bytes) -> Outcome:
        started = time.perf_counter()
        frame = decode(data)
        base = self.doc.version if self.doc else 0
        content = self.doc.content_bbox if self.doc else FULL_FRAME
        if self.frame is not None and same_frame(self.frame, frame, content):
            return Outcome("unchanged", self.doc, base)

        model_ms = 0
        candidate: Document | None = None
        mode: Mode = "full"
        for cached_frame, cached_doc in self.cache:
            if same_frame(cached_frame, frame, content):
                candidate, mode = cached_doc, "cache"
                break

        verified: set[str] = set()
        cross_checked = False
        if candidate is None:
            change = compare(self.frame, frame, content)
            layout = self.frame is not None and compare(self.frame, frame, FULL_FRAME).fraction > 0.5
            region_ok = (
                self.doc is not None
                and not layout
                and self.doc.content_type in ("sheet", "code")
                and change.fraction <= self.settings.full_reconstruct_threshold
                and change.bbox is not None
            )
            if region_ok:
                try:
                    result = await self._region(frame, change.bbox)  # type: ignore[arg-type]
                    if result is None:
                        self.frame = frame
                        return Outcome("ignored", self.doc, base, total_ms=self._ms(started))
                    candidate, model_ms, verified = result
                    mode = "region"
                except RegionMismatchError as exc:
                    log.info("region read fell back to full: %s", exc)
            if candidate is None:
                within = FULL_FRAME if self.doc is None or layout else pad(self.doc.content_bbox, 10, 10)
                candidate, model_ms, cross_checked = await self._full(frame, within)
                mode = "full"

        aligned = aligner.align(self.doc, candidate, self.minter)
        doc, changes = aligned.doc, aligned.changes
        if mode == "full" and self.doc is not None and not cross_checked:
            doc, changes, verify_ms = await self._verify_changes(frame, doc, changes, verified)
            model_ms += verify_ms

        self.frame = frame
        self.cache.appendleft((frame, doc))
        if not changes and self.doc is not None:
            return Outcome(mode, self.doc, base, model_ms=model_ms, total_ms=self._ms(started))
        prev = self.doc
        self.doc = doc
        ops = diff(prev.model_dump(mode="json"), doc.model_dump(mode="json")) if prev else []
        return Outcome(
            mode=mode,
            doc=doc,
            base=base,
            ops=ops,
            announces=announcements(changes, doc.version, self.numeric_style, self.focus_ref),
            model_ms=model_ms,
            total_ms=self._ms(started),
        )

    @staticmethod
    def _ms(started: float) -> int:
        return int((time.perf_counter() - started) * 1000)

    async def _full(self, frame: DecodedFrame, within: Box) -> tuple[Document, int, bool]:
        """-> (candidate, model ms, whether every value was cross-checked by a second read)."""
        doc, ms, checked = await self._full_pair(frame, within)
        tighter = doc.content_bbox
        if self.doc is None and area(tighter) < TIGHTEN_RATIO * area(within):
            # First frame inside a meeting window: re-read the content alone at higher resolution.
            crop_box = pad(tighter, 4, 4)
            doc, ms2, checked = await self._full_pair(frame, crop_box)
            doc = doc.model_copy(update={"content_bbox": tighter})
            ms += ms2
        return doc, ms, checked

    async def _full_pair(self, frame: DecodedFrame, within: Box) -> tuple[Document, int, bool]:
        if not self.settings.cross_check_full_reads:
            timed = await self.reader.full(frame, within)
            return build_document(timed.value, within), timed.latency_ms, False
        primary, second = await asyncio.gather(
            self.reader.full(frame, within),
            self.reader.full(frame, within, cross_check=True),
            return_exceptions=True,
        )
        if isinstance(primary, BaseException):
            raise primary
        doc = build_document(primary.value, within)
        if isinstance(second, BaseException):
            log.warning("cross-check read failed; changed values will be verified instead: %s", second)
            return doc, primary.latency_ms, False
        result = cross_check(doc, build_document(second.value, within))
        if result.disagreed:
            log.info("cross-check: %d of %d values disagreed and are marked unclear", result.disagreed, result.compared)
        return result.doc, max(primary.latency_ms, second.latency_ms), True

    async def _region(self, frame: DecodedFrame, changed: Box) -> tuple[Document, int, set[str]] | None:
        assert self.doc is not None
        if self.doc.sheet is not None:
            return await self._region_sheet(frame, changed)
        if self.doc.code is not None:
            return await self._region_code(frame, changed)
        raise RegionMismatchError("no structured content")

    async def _region_sheet(self, frame: DecodedFrame, changed: Box) -> tuple[Document, int, set[str]] | None:
        assert self.doc is not None and self.doc.sheet is not None
        sheet = self.doc.sheet
        if not sheet.rows:
            raise RegionMismatchError("empty sheet")
        table = union([c.bbox for c in sheet.columns] + [r.cells[0].bbox for r in sheet.rows if r.cells])
        assert table is not None
        row_h = max(6, (sheet.rows[0].cells[0].bbox.y1 - sheet.rows[0].cells[0].bbox.y0) if sheet.rows[0].cells else 20)
        if changed.y1 <= table.y0 - 2:
            return None  # toolbar, formula bar or title area: not table content
        if changed.y1 > table.y1 + row_h // 2 or changed.x1 > table.x1 + 20 or changed.y0 < sheet.columns[0].bbox.y1:
            raise RegionMismatchError("change outside known rows, or in the header")
        rows = [
            i
            for i, r in enumerate(sheet.rows)
            if r.cells and r.cells[0].bbox.y1 > changed.y0 and r.cells[0].bbox.y0 < changed.y1
        ]
        cols = [j for j, c in enumerate(sheet.columns) if c.bbox.x1 > changed.x0 and c.bbox.x0 < changed.x1]
        if not rows or not cols:
            return None
        boxes = [sheet.rows[i].cells[j].bbox for i in rows for j in cols]
        region = pad(union(boxes) or changed, 4, 3)
        headers = [sheet.columns[j].text for j in cols]
        keys = None if 0 in cols else [sheet.rows[i].key or f"row {i + 1}" for i in rows]
        region_task = self.reader.sheet_region(frame, region, headers, len(rows), keys)
        if len(boxes) <= self.settings.verify_max_items:
            region_read, verify = await asyncio.gather(region_task, self.reader.verify(frame, boxes, "cell"))
            checks: list[Reading] | None = verify.value
            ms = max(region_read.latency_ms, verify.latency_ms)
        else:
            region_read, checks = await region_task, None
            ms = region_read.latency_ms
        got = region_read.value.rows
        leg = legibility_of(region_read.value.unclear)
        if len(got) != len(rows) or any(len(r.cells) != len(cols) for r in got):
            raise RegionMismatchError(f"expected {len(rows)}x{len(cols)} cells")
        new_rows = list(sheet.rows)
        verified: set[str] = set()
        for a, i in enumerate(rows):
            cells = list(new_rows[i].cells)
            for b, j in enumerate(cols):
                read = ReadCell(text=got[a].cells[b], legibility=leg.get((a, b), "clear"))
                if checks is not None:
                    read = _merge_reading(read, checks[a * len(cols) + b])
                    verified.add(cells[j].id)
                cells[j] = cell_from(read, cells[j].bbox).model_copy(update={"id": cells[j].id})
            key = cells[0].text if cells and not cells[0].unreadable and cells[0].text else None
            new_rows[i] = new_rows[i].model_copy(update={"cells": cells, "key": key})
        candidate = self.doc.model_copy(update={"sheet": sheet.model_copy(update={"rows": new_rows})})
        return candidate, ms, verified

    async def _region_code(self, frame: DecodedFrame, changed: Box) -> tuple[Document, int, set[str]] | None:
        assert self.doc is not None and self.doc.code is not None
        lines = self.doc.code.lines
        if not lines:
            raise RegionMismatchError("no lines")
        last = lines[-1].bbox
        if changed.y1 < lines[0].bbox.y0:
            return None
        if changed.y1 > last.y1 + (last.y1 - last.y0):
            raise RegionMismatchError("change below the last known line")
        hit = [i for i, ln in enumerate(lines) if ln.bbox.y1 > changed.y0 and ln.bbox.y0 < changed.y1]
        if not hit:
            return None
        hit = list(range(hit[0], hit[-1] + 1))
        boxes = [lines[i].bbox for i in hit]
        region = pad(union(boxes) or changed, 2, 2)
        region_task = self.reader.code_region(frame, region, lines[hit[0]].n, len(hit))
        if len(boxes) <= self.settings.verify_max_items:
            region_read, verify = await asyncio.gather(region_task, self.reader.verify(frame, boxes, "line"))
            checks: list[Reading] | None = verify.value
            ms = max(region_read.latency_ms, verify.latency_ms)
        else:
            region_read, checks = await region_task, None
            ms = region_read.latency_ms
        got = region_read.value.lines
        leg = legibility_of(region_read.value.unclear)
        if len(got) != len(hit):
            raise RegionMismatchError(f"expected {len(hit)} lines, got {len(got)}")
        new_lines = list(lines)
        verified: set[str] = set()
        for a, i in enumerate(hit):
            read = got[a]
            legibility = leg.get((a, 0), "clear")
            if checks is not None:
                merged = _merge_reading(ReadCell(text=read.text, legibility=legibility), checks[a])
                legibility = merged.legibility
                verified.add(lines[i].id)
            old = lines[i]
            conf, unreadable, uncertain = flags(legibility)
            text = "" if unreadable else read.text.replace("\t", "    ").rstrip()
            new_lines[i] = old.model_copy(
                update={"text": text, "confidence": conf, "unreadable": unreadable, "uncertain": uncertain}
            )
        candidate = self.doc.model_copy(update={"code": self.doc.code.model_copy(update={"lines": new_lines})})
        return candidate, ms, verified

    async def _verify_changes(
        self, frame: DecodedFrame, doc: Document, changes: list[Change], verified: set[str]
    ) -> tuple[Document, list[Change], int]:
        """Second, differently worded read of every changed value on a tight 2x crop."""
        items: dict[str, Cell | CodeLine] = {}
        if doc.sheet:
            items.update({c.id: c for r in doc.sheet.rows for c in r.cells})
            items.update({c.id: c for c in doc.sheet.columns})
        if doc.code:
            items.update({ln.id: ln for ln in doc.code.lines})
        targets: list[tuple[int, str, Cell | CodeLine]] = []
        for k, c in enumerate(changes):
            if not isinstance(c, CellChanged | LineChanged) or c.uncertain or c.unreadable:
                continue
            ref = c.cell_id if isinstance(c, CellChanged) else c.line_id
            item = items.get(ref)
            if item is not None and ref not in verified:
                targets.append((k, ref, item))
        targets = targets[: self.settings.verify_max_items]
        if not targets:
            return doc, changes, 0
        kind = "cell" if doc.sheet else "line"
        try:
            timed = await self.reader.verify(frame, [item.bbox for _, _, item in targets], kind)
            readings, ms = timed.value, timed.latency_ms
        except ModelError as exc:
            log.warning("verification failed, marking %d changes uncertain: %s", len(targets), exc)
            readings, ms = [Reading(text="", legibility="unreadable")] * len(targets), 0
        uncertain_ids: set[str] = set()
        new_changes = list(changes)
        for (k, ref, item), reading in zip(targets, readings, strict=True):
            merged = _merge_reading(ReadCell(text=item.text, legibility="clear"), reading)
            if merged.legibility != "clear":
                uncertain_ids.add(ref)
                change = changes[k]
                if isinstance(change, CellChanged | LineChanged):
                    new_changes[k] = replace(change, uncertain=True)
        if not uncertain_ids:
            return doc, changes, ms
        return _mark_uncertain(doc, uncertain_ids), new_changes, ms

    def map_pointer(self, x: int, y: int) -> tuple[str | None, str]:
        return describe_pointer(self.doc, x, y)


def _mark_uncertain(doc: Document, ids: set[str]) -> Document:
    if doc.sheet:
        rows = [
            r.model_copy(
                update={
                    "cells": [
                        c.model_copy(update={"uncertain": True, "confidence": 0.5}) if c.id in ids else c
                        for c in r.cells
                    ]
                }
            )
            for r in doc.sheet.rows
        ]
        return doc.model_copy(update={"sheet": doc.sheet.model_copy(update={"rows": rows})})
    if doc.code:
        lines = [
            ln.model_copy(update={"uncertain": True, "confidence": 0.5}) if ln.id in ids else ln
            for ln in doc.code.lines
        ]
        return doc.model_copy(update={"code": doc.code.model_copy(update={"lines": lines})})
    return doc
