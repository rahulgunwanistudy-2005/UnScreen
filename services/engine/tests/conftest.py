from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_budget(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock-provider tests must never consume the real daily spending ledger."""
    monkeypatch.setenv("UNSCREEN_BUDGET_PATH", str(tmp_path / "budget.sqlite3"))
