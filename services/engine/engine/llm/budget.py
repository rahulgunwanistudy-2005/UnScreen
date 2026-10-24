"""Atomic daily estimated-spend reservations shared by engine and benchmark processes.

The ledger contains counts and dollars only, never prompts, frames or credentials.
UTC days match the documented reset. A failed/timed-out attempt keeps its reservation:
the provider may have billed it. This is an estimated cost guard, not a billing API.
"""

import json
import sqlite3
from collections.abc import Callable
from datetime import UTC, datetime

from engine.config import Settings
from engine.llm.client import ModelError, VisionRequest, VisionResult
from engine.llm.cost import PRICES_PER_MTOK, cost_usd


class DailyBudget:
    def __init__(self, settings: Settings, day: Callable[[], str] | None = None) -> None:
        self.settings = settings
        self.day = day or (lambda: datetime.now(UTC).date().isoformat())

    def reserve(self, model: str, request: VisionRequest | None = None) -> tuple[str, float]:
        try:
            return self._reserve(model, request)
        except (OSError, sqlite3.Error) as exc:
            raise ModelError("daily limit: spending ledger unavailable", status=429, quota_exhausted=True) from exc

    def _reserve(self, model: str, request: VisionRequest | None) -> tuple[str, float]:
        if model not in PRICES_PER_MTOK:
            raise ModelError("daily limit: model has no verified USD price", status=429, quota_exhausted=True)
        day, amount = self.day(), self.settings.model_call_reserve_usd
        if request is not None:
            # Text bytes overestimate ordinary token counts; reserve 8192 tokens
            # per image, plus the enforced 8192-token output ceiling. Estimates
            # are reconciled to provider usage on success, never called invoices.
            text_bytes = len((request.system + request.prompt + json.dumps(request.schema)).encode())
            price_in, price_out = PRICES_PER_MTOK[model]
            estimate = ((text_bytes + 8192 * len(request.images)) * price_in + 8192 * price_out) / 1_000_000
            amount = max(amount, estimate)
        self.settings.budget_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.settings.budget_path, timeout=10) as db:
            db.execute("CREATE TABLE IF NOT EXISTS daily (day TEXT PRIMARY KEY, calls INTEGER, usd REAL)")
            db.execute("BEGIN IMMEDIATE")
            db.execute("INSERT OR IGNORE INTO daily VALUES (?, 0, 0)", (day,))
            calls, usd = db.execute("SELECT calls, usd FROM daily WHERE day = ?", (day,)).fetchone()
            if calls >= self.settings.daily_model_calls or usd + amount > self.settings.daily_model_usd + 1e-9:
                raise ModelError("daily limit reached (resets at 00:00 UTC)", status=429, quota_exhausted=True)
            db.execute("UPDATE daily SET calls = calls + 1, usd = usd + ? WHERE day = ?", (amount, day))
        return day, amount

    def settle(self, reservation: tuple[str, float], result: VisionResult) -> None:
        actual = cost_usd(result)
        if actual is None:
            return  # fail closed: retain the reservation
        day, amount = reservation
        with sqlite3.connect(self.settings.budget_path, timeout=10) as db:
            db.execute("UPDATE daily SET usd = MAX(0, usd + ?) WHERE day = ?", (actual - amount, day))
