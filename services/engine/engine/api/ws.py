"""WebSocket /v1/session/{id}/ws: frames in, snapshots, patches and announcements out.

At most one frame is processed per session at a time; a newer frame replaces any queued one."""

import asyncio
import logging
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, TypeAdapter, ValidationError

from engine.config import Settings
from engine.llm.client import ModelError
from engine.model.protocol import (
    Answer,
    Ask,
    ClientMessage,
    Error,
    ErrorCode,
    Frame,
    Hello,
    PointerMsg,
    PointerTarget,
    Snapshot,
    Status,
)
from engine.model.protocol import Patch as PatchMsg
from engine.model.protocol import (
    Settings as SettingsMsg,
)
from engine.pipeline.ask import ask as run_ask
from engine.pipeline.frames import BadFrameError
from engine.store.sessions import Session, SessionStore

log = logging.getLogger(__name__)
router = APIRouter()
client_message: TypeAdapter[ClientMessage] = TypeAdapter(ClientMessage)


class Connection:
    def __init__(self, ws: WebSocket, session: Session, settings: Settings) -> None:
        self.ws = ws
        self.session = session
        self.settings = settings
        self.pending: tuple[Frame, bytes] | None = None
        self.wake = asyncio.Event()
        self.send_lock = asyncio.Lock()
        self.tasks: set[asyncio.Task[None]] = set()

    async def send(self, msg: BaseModel) -> None:
        async with self.send_lock:
            await self.ws.send_text(msg.model_dump_json())

    async def error(self, code: ErrorCode, message: str) -> None:
        await self.send(Error(code=code, message=message))

    async def worker(self) -> None:
        pipeline = self.session.pipeline
        while True:
            await self.wake.wait()
            self.wake.clear()
            if self.pending is None:
                continue
            frame, data = self.pending
            self.pending = None
            breaker = self.session.breaker
            if breaker.is_open():
                await self.send(
                    Status(stage="busy", detail="Content unchanged, engine busy.", latency_ms=None, content_bbox=None)
                )
                continue
            await self.send(Status(stage="reconstruct", detail=None, latency_ms=None, content_bbox=None))
            started = time.perf_counter()
            try:
                outcome = await pipeline.process(data)
            except BadFrameError as exc:
                await self.error("bad_frame", str(exc))
                continue
            except ModelError as exc:
                log.warning("session %s model failure: %s", self.session.id, exc)
                opened = breaker.failure()
                if opened:
                    await self.error(
                        "engine_busy",
                        "The reading engine is having trouble. The last version stays on screen, "
                        "and nothing new is announced until it recovers.",
                    )
                else:
                    await self.error("model_error", "Could not read that frame. Trying again with the next change.")
                await self.send(Status(stage="idle", detail=None, latency_ms=None, content_bbox=None))
                continue
            breaker.success()
            latency = int((time.perf_counter() - started) * 1000)
            doc = outcome.doc
            if doc is not None and outcome.base == 0 and outcome.changed:
                await self.send(Snapshot(version=doc.version, doc=doc))
            elif doc is not None and outcome.ops:
                await self.send(PatchMsg(version=doc.version, base=outcome.base, ops=outcome.ops))
            for a in outcome.announces:
                await self.send(a)
            await self.send(
                Status(
                    stage="idle",
                    latency_ms=latency,
                    detail=outcome.mode,
                    content_bbox=doc.content_bbox if doc else None,
                )
            )
            log.info(
                "session=%s frame=%d mode=%s model_ms=%d total_ms=%d cost_usd=%.5f",
                self.session.id,
                frame.seq,
                outcome.mode,
                outcome.model_ms,
                latency,
                pipeline.meter.usd,
            )

    async def handle(self, msg: ClientMessage) -> None:
        pipeline = self.session.pipeline
        match msg:
            case Hello(resume_version=resume):
                doc = pipeline.doc
                if doc is not None and resume != doc.version:
                    await self.send(Snapshot(version=doc.version, doc=doc))
                await self.send(
                    Status(
                        stage="idle", detail="ready", latency_ms=None, content_bbox=doc.content_bbox if doc else None
                    )
                )
            case Frame():
                raise AssertionError("frames are handled by the receive loop")
            case PointerMsg(xy=xy):
                ref, text = pipeline.map_pointer(xy.x, xy.y)
                await self.send(PointerTarget(ref=ref, text=text))
            case SettingsMsg(numeric_style=style, focus_ref=focus):
                pipeline.numeric_style = style
                pipeline.focus_ref = focus
            case Ask(q=q):
                if not self.session.asks.take():
                    await self.error("rate_limited", "Too many questions. Wait a few seconds and ask again.")
                    return
                if pipeline.doc is None or pipeline.frame is None:
                    await self.send(
                        Answer(
                            q=q, text="Nothing is being read yet, so there is nothing to ask about.", refs=[], version=0
                        )
                    )
                    return
                task = asyncio.create_task(self._answer(q))
                self.tasks.add(task)
                task.add_done_callback(self.tasks.discard)

    async def _answer(self, q: str) -> None:
        pipeline = self.session.pipeline
        doc, frame = pipeline.doc, pipeline.frame
        if doc is None or frame is None:
            return
        try:
            result = await run_ask(pipeline.reader, frame, doc, q)
        except ModelError as exc:
            log.warning("ask failed: %s", exc)
            await self.send(
                Answer(
                    q=q,
                    text="Sorry, the question could not be answered right now. Try again.",
                    refs=[],
                    version=doc.version,
                )
            )
            return
        await self.send(Answer(q=q, text=result.text, refs=result.refs, version=doc.version))


@router.websocket("/v1/session/{session_id}/ws")
async def session_socket(ws: WebSocket, session_id: str) -> None:
    store: SessionStore = ws.app.state.store
    settings: Settings = ws.app.state.settings
    origin = ws.headers.get("origin")
    session = store.get(session_id)
    token = ws.query_params.get("token", "")
    if origin is not None and origin not in settings.allowed_origins:
        await ws.close(code=4403, reason="origin not allowed")
        return
    if session is None or not session.check_token(token):
        await ws.close(code=4401, reason="unknown or expired session")
        return
    await ws.accept()
    session.connected = True
    conn = Connection(ws, session, settings)
    worker = asyncio.create_task(conn.worker())
    expecting: Frame | None = None
    try:
        while True:
            raw = await ws.receive()
            if raw["type"] == "websocket.disconnect":
                break
            session.touch()
            if raw.get("bytes") is not None:
                data: bytes = raw["bytes"]
                if expecting is None:
                    await conn.error("bad_message", "Binary data must follow a frame message.")
                    continue
                frame, expecting = expecting, None
                if len(data) > settings.max_frame_bytes:
                    await conn.error("bad_frame", "Frame too large.")
                    continue
                if not session.frames.take():
                    await conn.error("rate_limited", "Frames are arriving too fast; some are being skipped.")
                    continue
                conn.pending = (frame, data)
                conn.wake.set()
                continue
            text = raw.get("text")
            if text is None:
                continue
            try:
                msg = client_message.validate_json(text)
            except ValidationError as exc:
                await conn.error("bad_message", f"Invalid message: {exc.error_count()} problems.")
                continue
            if isinstance(msg, Frame):
                expecting = msg
            else:
                await conn.handle(msg)
    except WebSocketDisconnect:
        pass
    finally:
        session.connected = False
        session.touch()
        worker.cancel()
