"""Token-based cost accounting. Prices from https://ai.google.dev/gemini-api/docs/pricing
(fetched 2026-10-21, paid tier, USD per 1M tokens; thinking billed as output)."""

from dataclasses import dataclass, field

from engine.llm.client import VisionResult

PRICES_PER_MTOK: dict[str, tuple[float, float]] = {
    # https://console.groq.com/docs/model/qwen/qwen3.8-27b (fetched 2026-10-22)
    "groq:qwen/qwen3.8-27b": (0.80, 4.00),
    "gemini-3.8-flash": (0.75, 3.75),
    "gemini-3.6-flash": (0.75, 3.75),
    "gemini-3-flash-preview": (0.50, 3.00),
    "gemini-3.5-flash-lite": (0.30, 2.50),
    "gemini-3.1-flash-lite": (0.25, 1.50),
    "gemini-3.1-pro-preview": (2.00, 12.00),
}


def cost_usd(result: VisionResult) -> float | None:
    """None when no published price is on record for the model (we never guess one)."""
    prices = PRICES_PER_MTOK.get(result.model)
    if prices is None:
        return None
    price_in, price_out = prices
    out_tokens = result.usage.output_tokens + result.usage.thought_tokens
    return (result.usage.input_tokens * price_in + out_tokens * price_out) / 1_000_000


@dataclass
class CostMeter:
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    thought_tokens: int = 0
    usd: float = 0.0
    unpriced_calls: int = 0
    by_purpose: dict[str, float] = field(default_factory=dict)

    def add(self, purpose: str, result: VisionResult) -> None:
        self.calls += 1
        self.input_tokens += result.usage.input_tokens
        self.output_tokens += result.usage.output_tokens
        self.thought_tokens += result.usage.thought_tokens
        c = cost_usd(result)
        if c is None:
            self.unpriced_calls += 1
            return
        self.usd += c
        self.by_purpose[purpose] = self.by_purpose.get(purpose, 0.0) + c
