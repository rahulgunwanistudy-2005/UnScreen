"""Vision model access behind one small protocol, with record and replay for golden tests."""

import asyncio
import base64
import hashlib
import json
import logging
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

import httpx
from google import genai
from google.genai import errors as genai_errors
from google.genai._gaos.errors import GenAiError
from google.genai._gaos.lib.compat_errors import GeminiNextGenAPIClientError

from engine.config import Settings

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ImagePart:
    data: bytes
    mime: str


@dataclass(frozen=True)
class VisionRequest:
    purpose: str
    model: str
    system: str
    prompt: str
    schema: dict[str, Any]
    images: tuple[ImagePart, ...] = ()
    resolution: str = "high"
    thinking_level: str = "low"

    def key(self) -> str:
        body = {
            "model": self.model,
            "system": self.system,
            "prompt": self.prompt,
            "schema": self.schema,
            "images": [hashlib.sha256(i.data).hexdigest() for i in self.images],
            "resolution": self.resolution,
            "thinking": self.thinking_level,
        }
        return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:32]


@dataclass(frozen=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    thought_tokens: int = 0


@dataclass(frozen=True)
class VisionResult:
    text: str
    model: str
    usage: Usage = field(default_factory=Usage)
    latency_ms: int = 0
    replayed: bool = False


RETRYABLE_ERRORS = (genai_errors.APIError, GenAiError, GeminiNextGenAPIClientError, httpx.TransportError, TimeoutError)


class ModelError(Exception):
    """The model call failed after retries, or returned something unusable."""

    def __init__(
        self, message: str, *, retryable: bool = False, status: int | None = None, quota_exhausted: bool = False
    ) -> None:
        super().__init__(message)
        self.retryable = retryable
        self.status = status
        self.quota_exhausted = quota_exhausted


class GoldenMissingError(ModelError):
    pass


class VisionModel(Protocol):
    async def generate(self, request: VisionRequest) -> VisionResult: ...


def _is_daily_quota(exc: Exception) -> bool:
    """A 429 for a per-day quota will not clear within any sensible retry window."""
    text = str(exc)
    return "PerDay" in text or "free_tier_requests" in text


def _status_of(exc: Exception) -> int | None:
    for attr in ("status_code", "code"):
        value = getattr(exc, attr, None)
        if isinstance(value, int):
            return value
    return None


class GeminiVisionModel:
    def __init__(self, settings: Settings) -> None:
        if settings.gemini_api_key is None:
            raise ModelError("GEMINI_API_KEY is not set")
        self._client = genai.Client(api_key=settings.gemini_api_key.get_secret_value())
        self._timeout = settings.llm_timeout_s
        self._retries = settings.llm_max_retries

    async def generate(self, request: VisionRequest) -> VisionResult:
        content: list[dict[str, Any]] = [{"type": "text", "text": request.prompt}]
        for image in request.images:
            content.append(
                {
                    "type": "image",
                    "mime_type": image.mime,
                    "data": base64.b64encode(image.data).decode("ascii"),
                    "resolution": request.resolution,
                }
            )
        attempt = 0
        while True:
            started = time.perf_counter()
            try:
                interaction = await asyncio.wait_for(
                    self._client.aio.interactions.create(
                        model=request.model,
                        input=content,
                        system_instruction=request.system,
                        generation_config={"thinking_level": request.thinking_level},
                        response_format={
                            "type": "text",
                            "mime_type": "application/json",
                            "schema": request.schema,
                        },
                    ),
                    timeout=self._timeout,
                )
            except RETRYABLE_ERRORS as exc:
                status = _status_of(exc)
                if status == 429 and _is_daily_quota(exc):
                    raise ModelError(
                        f"{request.purpose}: daily quota exhausted", status=429, quota_exhausted=True
                    ) from exc
                retryable = status is None or status == 429 or status >= 500
                attempt += 1
                if not retryable or attempt > self._retries:
                    raise ModelError(
                        f"{request.purpose}: {type(exc).__name__} {status}", retryable=retryable, status=status
                    ) from exc
                delay = min(8.0, 0.5 * 2**attempt) * (0.75 + random.random() / 2)
                log.warning("model %s failed (%s), retry %d in %.1fs", request.purpose, status, attempt, delay)
                await asyncio.sleep(delay)
                continue
            latency_ms = int((time.perf_counter() - started) * 1000)
            text = getattr(interaction, "output_text", None)
            if not text:
                raise ModelError(f"{request.purpose}: empty response")
            usage = getattr(interaction, "usage", None)
            return VisionResult(
                text=text,
                model=request.model,
                latency_ms=latency_ms,
                usage=Usage(
                    input_tokens=getattr(usage, "total_input_tokens", None) or 0,
                    output_tokens=getattr(usage, "total_output_tokens", None) or 0,
                    thought_tokens=getattr(usage, "total_thought_tokens", None) or 0,
                ),
            )


class ReplayVisionModel:
    """Serves recorded responses. Used by CI, which never calls the live API."""

    def __init__(self, golden_dir: Path) -> None:
        self._dir = golden_dir

    async def generate(self, request: VisionRequest) -> VisionResult:
        path = self._dir / f"{request.key()}.json"
        if not path.exists():
            raise GoldenMissingError(f"no recorded response for {request.purpose} ({path.name})")
        data = json.loads(path.read_text())
        return VisionResult(
            text=data["text"],
            model=data["model"],
            usage=Usage(**data["usage"]),
            latency_ms=data["latency_ms"],
            replayed=True,
        )


class RecordingVisionModel:
    """Replays a response already on disk; otherwise calls the live model and stores the result."""

    def __init__(self, inner: VisionModel, golden_dir: Path) -> None:
        self._inner = inner
        self._dir = golden_dir
        self._dir.mkdir(parents=True, exist_ok=True)
        self._replay = ReplayVisionModel(golden_dir)

    async def generate(self, request: VisionRequest) -> VisionResult:
        if (self._dir / f"{request.key()}.json").exists():
            return await self._replay.generate(request)
        result = await self._inner.generate(request)
        record = {
            "purpose": request.purpose,
            "model": result.model,
            "text": result.text,
            "latency_ms": result.latency_ms,
            "usage": {
                "input_tokens": result.usage.input_tokens,
                "output_tokens": result.usage.output_tokens,
                "thought_tokens": result.usage.thought_tokens,
            },
        }
        (self._dir / f"{request.key()}.json").write_text(json.dumps(record, indent=1) + "\n")
        return result


def build_model(settings: Settings) -> VisionModel:
    if settings.llm_mode == "replay":
        return ReplayVisionModel(settings.golden_dir)
    live = GeminiVisionModel(settings)
    if settings.llm_mode == "record":
        return RecordingVisionModel(live, settings.golden_dir)
    return live
