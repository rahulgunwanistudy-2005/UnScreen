import json
from pathlib import Path

from engine.model.export import build_schema, main

COMMITTED = Path(__file__).resolve().parents[4] / "packages" / "schema" / "unscreen.schema.json"


def test_schema_has_every_wire_type_and_no_property_titles() -> None:
    schema = build_schema()
    defs = schema["$defs"]
    for name in ("Document", "Snapshot", "Patch", "Announce", "Frame", "Hello", "Ask", "SessionGrant"):
        assert name in defs
    for d in defs.values():
        for prop in d.get("properties", {}).values():
            assert "title" not in prop
    assert "type" in defs["Snapshot"]["required"]


def test_committed_schema_matches_models() -> None:
    assert json.loads(COMMITTED.read_text()) == json.loads(json.dumps(build_schema(), sort_keys=True))


def test_cli_writes_file_and_rejects_bad_usage(tmp_path: Path) -> None:
    out = tmp_path / "s.json"
    assert main(["export", str(out)]) == 0
    assert json.loads(out.read_text())["title"] == "UnScreenSchema"
    assert main(["export"]) == 2
