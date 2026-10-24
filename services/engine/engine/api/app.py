"""FastAPI app: thin wiring only."""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from engine.api.ws import router as ws_router
from engine.config import Settings, get_settings
from engine.llm.client import VisionModel, build_model
from engine.model.protocol import PROTOCOL_VERSION, SessionGrant
from engine.store.sessions import SessionLimitError, SessionStore

log = logging.getLogger("engine")


class Health(BaseModel):
    ok: bool
    protocol: str
    sessions: int
    llm_mode: str
    models: dict[str, str]
    cross_check: bool


def create_app(settings: Settings | None = None, model: VisionModel | None = None) -> FastAPI:
    settings = settings or get_settings()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.settings = settings
        app.state.store = SessionStore(settings, model or build_model(settings))

        async def janitor() -> None:
            while True:
                await asyncio.sleep(60)
                evicted = app.state.store.evict_expired()
                if evicted:
                    log.info("evicted %d expired sessions", evicted)

        task = asyncio.create_task(janitor())
        yield
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    app = FastAPI(title="UnScreen engine", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["content-type"],
    )

    @app.get("/healthz", response_model=Health)
    async def health(request: Request) -> Health:
        return Health(
            ok=True,
            protocol=PROTOCOL_VERSION,
            sessions=len(request.app.state.store),
            llm_mode=settings.llm_mode,
            models={
                "reconstruct": settings.reconstruct_model,
                "verify": settings.verify_model,
                "region": settings.region_model,
                "ask": settings.ask_model,
            },
            cross_check=settings.cross_check_full_reads,
        )

    @app.post("/v1/session", response_model=SessionGrant)
    async def new_session(request: Request) -> SessionGrant:
        ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (
            request.client.host if request.client else "unknown"
        )
        try:
            session = request.app.state.store.create(ip)
        except SessionLimitError as exc:
            raise HTTPException(status_code=429, detail=str(exc)) from exc
        return SessionGrant(
            session_id=session.id, token=session.token, expires_in_s=settings.session_ttl_s, protocol=PROTOCOL_VERSION
        )

    app.include_router(ws_router)
    return app


app = create_app()
