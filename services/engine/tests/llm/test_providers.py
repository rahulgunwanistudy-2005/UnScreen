import json
from typing import Any

import httpx
import pytest

from engine.config import Settings
from engine.llm.client import ImagePart, ModelError, VisionRequest
from engine.llm.providers import PROVIDERS, ChatVisionModel, max_images, split_model, strict_schema
from engine.llm.schemas import FullRead, response_schema


def settings() -> Settings:
    return Settings(gemini_api_key=None, llm_mode="live", llm_max_retries=2)


def request(model: str = "groq:qwen/qwen3.8-27b") -> VisionRequest:
    return VisionRequest(
        purpose="reconstruct",
        model=model,
        system="sys",
        prompt="read it",
        schema=response_schema(FullRead),
        images=(ImagePart(b"\x89PNG", "image/png"),),
    )


def ok(content: str = '{"a": 1}') -> httpx.Response:
    return httpx.Response(
        200,
        json={"choices": [{"message": {"content": content}}], "usage": {"prompt_tokens": 10, "completion_tokens": 4}},
    )


def test_split_model_and_image_limits() -> None:
    assert split_model("groq:qwen/qwen3.8-27b") == ("groq", "qwen/qwen3.8-27b")
    assert split_model("mistral:mistral-small-latest") == ("mistral", "mistral-small-latest")
    assert split_model("gemini-3.6-flash") == ("gemini", "gemini-3.6-flash")
    assert max_images("groq:qwen/qwen3.8-27b") == 3
    assert max_images("gemini-3.6-flash") > 3


def test_strict_schema_closes_objects_and_requires_every_field() -> None:
    schema = strict_schema(response_schema(FullRead))

    def check(node: Any) -> None:
        if isinstance(node, dict):
            if node.get("type") == "object" and "properties" in node:
                assert node["additionalProperties"] is False
                assert set(node["required"]) == set(node["properties"])
            for v in node.values():
                check(v)
        elif isinstance(node, list):
            for v in node:
                check(v)

    check(schema)
    assert "additionalProperties" not in response_schema(FullRead)


async def test_request_shape_and_usage() -> None:
    seen: list[dict[str, Any]] = []

    def handler(req: httpx.Request) -> httpx.Response:
        seen.append(json.loads(req.content))
        assert req.headers["authorization"] == "Bearer k"
        return ok()

    model = ChatVisionModel(PROVIDERS["groq"], "k", settings(), httpx.MockTransport(handler))
    result = await model.generate(request())
    body = seen[0]
    assert body["model"] == "qwen/qwen3.8-27b"
    image = body["messages"][1]["content"][1]
    assert image["image_url"]["url"].startswith("data:image/png;base64,")
    assert body["response_format"]["json_schema"]["strict"] is True
    assert body["reasoning_effort"] == "none" and body["max_completion_tokens"] == 1000
    assert result.text == '{"a": 1}' and result.usage.input_tokens == 10 and result.model == "groq:qwen/qwen3.8-27b"


async def test_server_error_is_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    async def no_sleep(_: float) -> None:
        return None

    monkeypatch.setattr("engine.llm.providers.asyncio.sleep", no_sleep)
    responses = iter([httpx.Response(503, text="busy"), ok()])
    model = ChatVisionModel(PROVIDERS["mistral"], "k", settings(), httpx.MockTransport(lambda _: next(responses)))
    assert (await model.generate(request("mistral:mistral-small-latest"))).text == '{"a": 1}'


async def test_long_quota_wait_fails_fast_and_bad_request_is_not_retried() -> None:
    calls = 0

    def quota(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(429, headers={"retry-after": "3600"}, text="quota")

    model = ChatVisionModel(PROVIDERS["groq"], "k", settings(), httpx.MockTransport(quota))
    with pytest.raises(ModelError) as err:
        await model.generate(request())
    assert err.value.quota_exhausted and calls == 1
    bad = ChatVisionModel(
        PROVIDERS["groq"], "k", settings(), httpx.MockTransport(lambda _: httpx.Response(400, text="no"))
    )
    with pytest.raises(ModelError) as err2:
        await bad.generate(request())
    assert err2.value.status == 400 and not err2.value.retryable


async def test_empty_message_is_an_error() -> None:
    model = ChatVisionModel(PROVIDERS["groq"], "k", settings(), httpx.MockTransport(lambda _: ok("")))
    with pytest.raises(ModelError):
        await model.generate(request())
