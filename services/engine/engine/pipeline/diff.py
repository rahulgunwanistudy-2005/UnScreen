"""Id-aware RFC 6902 diff. Lists of objects with an "id" are matched by id, so an edited cell
becomes one `replace` on its text and an inserted row one `add`; nothing else is touched."""

from difflib import SequenceMatcher
from typing import Any

from engine.model.protocol import PatchOp

Json = Any


def _esc(key: str) -> str:
    return key.replace("~", "~0").replace("/", "~1")


def _is_id_list(items: list[Json]) -> bool:
    return all(isinstance(i, dict) and isinstance(i.get("id"), str) and i["id"] for i in items)


def diff(a: Json, b: Json, path: str = "") -> list[PatchOp]:
    ops: list[PatchOp] = []
    _diff(a, b, path, ops)
    return ops


def _diff(a: Json, b: Json, path: str, ops: list[PatchOp]) -> None:
    if a == b:
        return
    if isinstance(a, dict) and isinstance(b, dict):
        for key in a:
            if key not in b:
                ops.append(PatchOp(op="remove", path=f"{path}/{_esc(key)}"))
        for key, value in b.items():
            if key not in a:
                ops.append(PatchOp(op="add", path=f"{path}/{_esc(key)}", value=value))
            else:
                _diff(a[key], value, f"{path}/{_esc(key)}", ops)
        return
    if isinstance(a, list) and isinstance(b, list):
        if a and b and _is_id_list(a) and _is_id_list(b):
            _diff_id_list(a, b, path, ops)
            return
        if len(a) == len(b):
            for i, (x, y) in enumerate(zip(a, b, strict=True)):
                _diff(x, y, f"{path}/{i}", ops)
            return
    ops.append(PatchOp(op="replace", path=path or "", value=b))


def _diff_id_list(a: list[Json], b: list[Json], path: str, ops: list[PatchOp]) -> None:
    a_ids = [x["id"] for x in a]
    b_ids = [x["id"] for x in b]
    matcher = SequenceMatcher(a=a_ids, b=b_ids, autojunk=False)
    matched_a: dict[int, int] = {}
    for block in matcher.get_matching_blocks():
        for k in range(block.size):
            matched_a[block.a + k] = block.b + k
    matched_b = {j: i for i, j in matched_a.items()}
    for i in range(len(a) - 1, -1, -1):
        if i not in matched_a:
            ops.append(PatchOp(op="remove", path=f"{path}/{i}"))
    for j, item in enumerate(b):
        if j in matched_b:
            _diff(a[matched_b[j]], item, f"{path}/{j}", ops)
        else:
            ops.append(PatchOp(op="add", path=f"{path}/{j}", value=item))
