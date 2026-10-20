"""Export the JSON Schema for the document model and wire protocol.

Usage: python -m engine.model.export <out.json>
"""

import json
import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from engine.model.document import Document
from engine.model.protocol import ClientMessage, ServerMessage, SessionGrant


class UnScreenSchema(BaseModel):
    """Root that pulls every wire type into one schema."""

    model_config = ConfigDict(title="UnScreenSchema")

    document: Document
    client_message: ClientMessage
    server_message: ServerMessage
    session_grant: SessionGrant


def _strip_property_titles(node: Any) -> None:
    """Pydantic titles every property; TS generators turn each into a junk alias."""
    if isinstance(node, dict):
        props = node.get("properties")
        if isinstance(props, dict):
            for prop in props.values():
                if isinstance(prop, dict):
                    prop.pop("title", None)
        for value in node.values():
            _strip_property_titles(value)
    elif isinstance(node, list):
        for item in node:
            _strip_property_titles(item)


def build_schema() -> dict[str, Any]:
    schema = UnScreenSchema.model_json_schema(mode="serialization")
    _strip_property_titles(schema)
    return schema


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python -m engine.model.export <out.json>", file=sys.stderr)
        return 2
    Path(argv[1]).write_text(json.dumps(build_schema(), indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
