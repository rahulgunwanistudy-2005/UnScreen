import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from engine.config import Settings
from engine.llm.budget import DailyBudget
from engine.llm.client import ModelError, Usage, VisionResult

MODEL = "gemini-3.6-flash"


def make(tmp_path: Path, **kwargs: object) -> DailyBudget:
    return DailyBudget(Settings(budget_path=tmp_path / "ledger.db", **kwargs))  # type: ignore[arg-type]


def test_shared_call_cap_survives_new_instances_and_resets_on_new_day(tmp_path: Path) -> None:
    guard = make(tmp_path, daily_model_calls=2)
    guard.day = lambda: "2026-10-24"
    guard.reserve(MODEL)
    other = make(tmp_path, daily_model_calls=2)
    other.day = guard.day
    other.reserve(MODEL)
    with pytest.raises(ModelError) as error:
        guard.reserve(MODEL)
    assert error.value.quota_exhausted
    guard.day = lambda: "2026-10-25"
    guard.reserve(MODEL)


def test_usd_reservations_settle_and_failed_calls_retain_the_estimate(tmp_path: Path) -> None:
    guard = make(tmp_path, daily_model_usd=0.15, model_call_reserve_usd=0.10)
    reservation = guard.reserve(MODEL)
    with pytest.raises(ModelError):
        guard.reserve(MODEL)
    guard.settle(reservation, VisionResult("{}", MODEL, Usage(1000, 200)))
    guard.reserve(MODEL)  # first successful call cost far less than the reservation
    with pytest.raises(ModelError):
        guard.reserve(MODEL)  # second, failed attempt retains its full reservation


def test_parallel_reservations_cannot_overshoot_call_cap(tmp_path: Path) -> None:
    guard = make(tmp_path, daily_model_calls=3)
    guard.reserve(MODEL)  # initialize before testing contention

    def attempt(_: int) -> bool:
        try:
            make(tmp_path, daily_model_calls=3).reserve(MODEL)
            return True
        except ModelError:
            return False

    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(attempt, range(8))) == 2
    with sqlite3.connect(guard.settings.budget_path) as db:
        assert db.execute("SELECT calls FROM daily").fetchone()[0] == 3


def test_zero_cap_and_unpriced_model_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(ModelError):
        make(tmp_path, daily_model_calls=0).reserve(MODEL)
    with pytest.raises(ModelError):
        make(tmp_path).reserve("unknown:unpriced")


def test_unavailable_ledger_fails_closed(tmp_path: Path) -> None:
    guard = DailyBudget(Settings(budget_path=tmp_path))  # a directory cannot be opened as SQLite
    with pytest.raises(ModelError) as error:
        guard.reserve(MODEL)
    assert error.value.quota_exhausted


def test_missing_provider_usage_retains_the_reservation(tmp_path: Path) -> None:
    guard = make(tmp_path, daily_model_usd=0.10, model_call_reserve_usd=0.10)
    reservation = guard.reserve(MODEL)
    guard.settle(reservation, VisionResult("{}", MODEL))
    with pytest.raises(ModelError):
        guard.reserve(MODEL)
