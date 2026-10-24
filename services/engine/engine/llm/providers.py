"""Mistral and Groq vision models through their OpenAI-compatible chat APIs, plus the router
that picks a provider from the model id prefix ("mistral:", "groq:"; no prefix means Gemini).

Request shapes verified 2026-10-22: Mistral OpenAPI spec (ImageURLChunk, JsonSchema) and
https://console.groq.com/docs/vision, /docs/structured-outputs."""

import asyncio
import base64
import copy
import logging
import random
import time
from dataclasses import dataclass
from typing import Any

import httpx

from engine.config import Settings
from engine.llm.client import GeminiVisionModel, ModelError, Usage, VisionModel, VisionRequest, VisionResult

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Provider:
    name: str
    base_url: str
    max_images: int
    extra: tuple[tuple[str, Any], ...] = ()
    """Provider-specific request fields."""


PROVIDERS: dict[str, Provider] = {
    "mistral": Provider("mistral", "https://api.mistral.ai/v1", max_images=8),
    # Qwen 3.8 on Groq reasons by default, which spends output tokens; the free tier allows
    # 1,000 output tokens per minute, so reasoning is turned off and output is capped.
    "groq": Provider(
        "groq",
        "https://api.groq.com/openai/v1",
        max_images=3,
        extra=(("reasoning_effort", "none"), ("max_completion_tokens", 1000)),
    ),
}
GEMINI_MAX_IMAGES = 32


def split_model(model: str) -> tuple[str, str]:
    """'groq:qwen/qwen3.8-27b' -> ('groq', 'qwen/qwen3.8-27b'); no prefix -> ('gemini', model)."""
    prefix, sep, rest = model.partition(":")
    if sep and prefix in PROVIDERS:
        return prefix, rest
    return "gemini", model


def max_images(model: str) -> int:
    provider, _ = split_model(model)
    return PROVIDERS[provider].max_images if provider in PROVIDERS else GEMINI_MAX_IMAGES


def strict_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Strict structured output needs closed objects with every property required."""
    out = copy.deepcopy(schema)

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if node.get("type") == "object" and isinstance(node.get("properties"), dict):
                node["additionalProperties"] = False
                node["required"] = list(node["properties"])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(out)
    return out


def _retry_after(response: httpx.Response) -> float | None:
    raw = response.headers.get("retry-after")
    try:
        return float(raw) if raw is not None else None
    except ValueError:
        return None


class ChatVisionModel:
    """One OpenAI-compatible provider."""

    def __init__(
        self, provider: Provider, api_key: str, settings: Settings, transport: httpx.AsyncBaseTransport | None = None
    ) -> None:
        self._provider = provider
        self._client = httpx.AsyncClient(
            base_url=provider.base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=settings.llm_timeout_s,
            transport=transport,
        )
        self._retries = settings.llm_max_retries
        from engine.llm.budget import DailyBudget

        self._budget = DailyBudget(settings)

    async def generate(self, request: VisionRequest) -> VisionResult:
        _, model = split_model(request.model)
        content: list[dict[str, Any]] = [{"type": "text", "text": request.prompt}]
        for image in request.images:
            data = base64.b64encode(image.data).decode("ascii")
            content.append({"type": "image_url", "image_url": {"url": f"data:{image.mime};base64,{data}"}})
        body = {
            "model": model,
            "messages": [{"role": "system", "content": request.system}, {"role": "user", "content": content}],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": request.purpose, "schema": strict_schema(request.schema), "strict": True},
            },
            "temperature": 0,
            **({"max_tokens": 8192} if self._provider.name != "groq" else {}),
            **dict(self._provider.extra),
        }
        attempt = 0
        while True:
            reservation = self._budget.reserve(request.model, request)
            started = time.perf_counter()
            try:
                response = await self._client.post("/chat/completions", json=body)
            except httpx.TransportError as exc:
                status: int | None = None
                detail = type(exc).__name__
                wait = None
            else:
                if response.status_code == 200:
                    result = self._result(request, response, started)
                    self._budget.settle(reservation, result)
                    return result
                status = response.status_code
                detail = response.text[:300]
                wait = _retry_after(response)
            attempt += 1
            retryable = status is None or status == 429 or status >= 500
            if status == 429 and wait is not None and wait > 60:
                raise ModelError(
                    f"{request.purpose}: {self._provider.name} quota exhausted", status=429, quota_exhausted=True
                )
            if not retryable or attempt > self._retries:
                raise ModelError(
                    f"{request.purpose}: {self._provider.name} {status} {detail}", retryable=retryable, status=status
                )
            delay = wait if wait is not None else min(8.0, 0.5 * 2**attempt) * (0.75 + random.random() / 2)
            log.warning(
                "%s %s failed (%s), retry %d in %.1fs", self._provider.name, request.purpose, status, attempt, delay
            )
            await asyncio.sleep(delay)

    def _result(self, request: VisionRequest, response: httpx.Response, started: float) -> VisionResult:
        data = response.json()
        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelError(f"{request.purpose}: {self._provider.name} returned no message") from exc
        if not text:
            raise ModelError(f"{request.purpose}: {self._provider.name} returned an empty message")
        usage = data.get("usage") or {}
        return VisionResult(
            text=text,
            model=request.model,
            latency_ms=int((time.perf_counter() - started) * 1000),
            usage=Usage(input_tokens=usage.get("prompt_tokens", 0), output_tokens=usage.get("completion_tokens", 0)),
        )


class RoutingVisionModel:
    """Sends each request to the provider named by its model id. Providers are built on first use."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._models: dict[str, VisionModel] = {}
        self._slots = asyncio.Semaphore(2)

    def _model_for(self, provider: str) -> VisionModel:
        if provider not in self._models:
            s = self._settings
            if provider == "gemini":
                self._models[provider] = GeminiVisionModel(s)
            else:
                key = s.mistral_api_key if provider == "mistral" else s.groq_api_key
                if key is None:
                    raise ModelError(f"{provider.upper()}_API_KEY is not set")
                self._models[provider] = ChatVisionModel(PROVIDERS[provider], key.get_secret_value(), s)
        return self._models[provider]

    async def generate(self, request: VisionRequest) -> VisionResult:
        provider, _ = split_model(request.model)
        async with self._slots:
            return await self._model_for(provider).generate(request)
