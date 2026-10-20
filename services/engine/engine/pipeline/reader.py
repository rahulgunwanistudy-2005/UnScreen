"""Model calls: full reconstruct, region re-read and verification reads."""

import logging
from dataclasses import dataclass

from pydantic import BaseModel, ValidationError

from engine.config import Settings
from engine.llm import prompts
from engine.llm.client import ImagePart, ModelError, VisionModel, VisionRequest, VisionResult
from engine.llm.cost import CostMeter
from engine.llm.schemas import (
    AskAnswer,
    CodeRegionRead,
    FullRead,
    Reading,
    SheetRegionRead,
    VerifyRead,
    response_schema,
)
from engine.model.document import FULL_FRAME, Box
from engine.pipeline.frames import DecodedFrame, crop, encode

log = logging.getLogger(__name__)

VERIFY_UPSCALE = 2.0
FULL_MAX_SIDE = 2048


@dataclass(frozen=True)
class Timed[T]:
    value: T
    latency_ms: int


class Reader:
    def __init__(self, model: VisionModel, settings: Settings, meter: CostMeter) -> None:
        self._model = model
        self._settings = settings
        self._meter = meter

    async def _call[M: BaseModel](
        self, purpose: str, model_id: str, prompt: str, schema_model: type[M], images: list[bytes], mime: str
    ) -> Timed[M]:
        request = VisionRequest(
            purpose=purpose,
            model=model_id,
            system=prompts.SYSTEM,
            prompt=prompt,
            schema=response_schema(schema_model),
            images=tuple(ImagePart(data=d, mime=mime) for d in images),
            resolution=self._settings.image_resolution,
            thinking_level=self._settings.thinking_level,
        )
        result: VisionResult = await self._model.generate(request)
        self._meter.add(purpose, result)
        try:
            parsed = schema_model.model_validate_json(result.text)
        except ValidationError as exc:
            raise ModelError(f"{purpose}: response did not match schema ({exc.error_count()} errors)") from exc
        return Timed(parsed, result.latency_ms)

    async def full(self, frame: DecodedFrame, within: Box) -> Timed[FullRead]:
        image = crop(frame, within)
        if max(image.size) > FULL_MAX_SIDE:
            image.thumbnail((FULL_MAX_SIDE, FULL_MAX_SIDE))
        data, mime = encode(image)
        return await self._call("reconstruct", self._settings.reconstruct_model, prompts.FULL, FullRead, [data], mime)

    async def sheet_region(
        self, frame: DecodedFrame, region: Box, headers: list[str], row_count: int, row_keys: list[str] | None
    ) -> Timed[SheetRegionRead]:
        data, mime = encode(crop(frame, region, upscale=1.5))
        prompt = prompts.sheet_region(headers, row_count, row_keys)
        return await self._call("region_sheet", self._settings.region_model, prompt, SheetRegionRead, [data], mime)

    async def code_region(
        self, frame: DecodedFrame, region: Box, first_n: int | None, line_count: int
    ) -> Timed[CodeRegionRead]:
        data, mime = encode(crop(frame, region, upscale=1.5))
        prompt = prompts.code_region(first_n, line_count)
        return await self._call("region_code", self._settings.region_model, prompt, CodeRegionRead, [data], mime)

    async def verify(self, frame: DecodedFrame, boxes: list[Box], kind: str) -> Timed[list[Reading]]:
        images = [encode(crop(frame, b, upscale=VERIFY_UPSCALE))[0] for b in boxes]
        timed = await self._call(
            f"verify_{kind}",
            self._settings.verify_model,
            prompts.verify(len(boxes), kind),
            VerifyRead,
            images,
            "image/png",
        )
        readings = timed.value.readings
        if len(readings) != len(boxes):
            log.warning("verify returned %d readings for %d crops", len(readings), len(boxes))
            readings = (readings + [Reading(text="", legibility="unreadable")] * len(boxes))[: len(boxes)]
        return Timed(readings, timed.latency_ms)

    async def ask(self, frame: DecodedFrame, doc_json: str, question: str) -> Timed[AskAnswer]:
        data, mime = encode(crop(frame, FULL_FRAME))
        prompt = prompts.ASK.format(doc=doc_json, question=question)
        return await self._call("ask", self._settings.ask_model, prompt, AskAnswer, [data], mime)
