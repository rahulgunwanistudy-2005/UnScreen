import pytest

from engine.llm.client import GoldenMissingError, ImagePart, RecordingVisionModel, ReplayVisionModel, VisionRequest
from engine.llm.cost import CostMeter, cost_usd
from engine.llm.schemas import FullRead, response_schema
from tests.factories import full_sheet_read
from tests.fakes import ScriptedModel


def request(img: bytes = b"x") -> VisionRequest:
    return VisionRequest(
        purpose="reconstruct",
        model="gemini-3.8-flash",
        system="s",
        prompt="p",
        schema=response_schema(FullRead),
        images=(ImagePart(img, "image/png"),),
    )


async def test_record_then_replay_roundtrip(tmp_path) -> None:  # type: ignore[no-untyped-def]
    inner = ScriptedModel()
    inner.push("reconstruct", full_sheet_read(["A"], [["1"]]))
    recorded = await RecordingVisionModel(inner, tmp_path).generate(request())
    replayed = await ReplayVisionModel(tmp_path).generate(request())
    assert replayed.text == recorded.text and replayed.replayed
    with pytest.raises(GoldenMissingError):
        await ReplayVisionModel(tmp_path).generate(request(b"other image"))


def test_request_key_depends_on_image_and_prompt() -> None:
    assert request(b"a").key() != request(b"b").key()
    assert request(b"a").key() == request(b"a").key()


def test_schema_is_inlined_and_untitled() -> None:
    schema = response_schema(FullRead)
    assert "$ref" not in str(schema) and "$defs" not in schema
    assert "title" in schema["properties"] and "title" not in schema["properties"]["title"]
    assert "title" not in schema
    assert schema["properties"]["content_box_2d"]["maxItems"] == 4


def test_cost_uses_published_prices() -> None:
    from engine.llm.client import Usage, VisionResult

    r = VisionResult(text="{}", model="gemini-3.8-flash", usage=Usage(1_000_000, 100_000, 100_000))
    assert cost_usd(r) == pytest.approx(0.75 + 0.2 * 3.75)
    meter = CostMeter()
    meter.add("reconstruct", r)
    assert meter.calls == 1 and meter.by_purpose["reconstruct"] == pytest.approx(cost_usd(r))
