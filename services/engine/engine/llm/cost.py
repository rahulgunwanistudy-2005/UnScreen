"""Token-based cost accounting. Prices from https://ai.google.dev/gemini-api/docs/pricing
(fetched 2026-10-21, paid tier, USD per 1M tokens; thinking billed as output)."""

from dataclasses import dataclass, field

from engine.llm.client import VisionResult

PRICES_PER_MTOK: dict[str, tuple[float, float]] = {
    "gemini-3.8-flash": (0.75, 3.75),
    "gemini-3.6-flash": (0.75, 3.75),
    "gemini-3-flash-preview": (0.50, 3.00),
    "gemini-3.5-flash-lite": (0.30, 2.50),
    "gemini-3.1-flash-lite": (0.25, 1.50),
    "gemini-3.1-pro-preview": (2.00, 12.00),
}


def cost_usd(result: VisionResult) -> float:
    price_in, price_out = PRICES_PER_MTOK.get(result.model, (0.0, 0.0))
    out_tokens = result.usage.output_tokens + result.usage.thought_tokens
    return (result.usage.input_tokens * price_in + out_tokens * price_out) / 1_000_000


@dataclass
class CostMeter:
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    thought_tokens: int = 0
    usd: float = 0.0
    by_purpose: dict[str, float] = field(default_factory=dict)

    def add(self, purpose: str, result: VisionResult) -> None:
        self.calls += 1
        self.input_tokens += result.usage.input_tokens
        self.output_tokens += result.usage.output_tokens
        self.thought_tokens += result.usage.thought_tokens
        c = cost_usd(result)
        self.usd += c
        self.by_purpose[purpose] = self.by_purpose.get(purpose, 0.0) + c
