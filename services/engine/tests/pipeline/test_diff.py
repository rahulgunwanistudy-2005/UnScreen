import copy
from typing import Any

import jsonpatch
from hypothesis import given, settings
from hypothesis import strategies as st

from engine.pipeline.align import IdMinter, align
from engine.pipeline.diff import diff
from tests.factories import candidate_code, candidate_sheet


def apply(doc: Any, ops: list[Any]) -> Any:
    return jsonpatch.apply_patch(copy.deepcopy(doc), [o.model_dump(exclude_none=False) for o in ops])


def test_scalar_and_nested_changes() -> None:
    a = {"x": 1, "y": {"z": [1, 2, 3]}, "gone": True}
    b = {"x": 2, "y": {"z": [1, 2, 4]}, "new": "v"}
    assert apply(a, diff(a, b)) == b


def test_id_list_edit_is_a_single_replace() -> None:
    a = {"rows": [{"id": "r1", "text": "a"}, {"id": "r2", "text": "b"}]}
    b = {"rows": [{"id": "r1", "text": "a"}, {"id": "r2", "text": "B"}]}
    ops = diff(a, b)
    assert [(o.op, o.path, o.value) for o in ops] == [("replace", "/rows/1/text", "B")]


def test_id_list_insert_and_remove_keep_other_items() -> None:
    a = {"rows": [{"id": "r1"}, {"id": "r2"}, {"id": "r3"}]}
    b = {"rows": [{"id": "r1"}, {"id": "r9"}, {"id": "r3"}, {"id": "r4"}]}
    ops = diff(a, b)
    assert {o.op for o in ops} == {"add", "remove"}
    assert apply(a, ops) == b


def test_keys_with_slash_and_tilde_are_escaped() -> None:
    a = {"a/b": 1, "c~d": 1}
    b = {"a/b": 2, "c~d": 2}
    assert apply(a, diff(a, b)) == b


json_scalars = st.one_of(st.none(), st.booleans(), st.integers(-5, 5), st.text(max_size=3))
json_values = st.recursive(
    json_scalars,
    lambda children: st.one_of(
        st.lists(children, max_size=4),
        st.dictionaries(st.text(max_size=3), children, max_size=4),
    ),
    max_leaves=12,
)


@settings(max_examples=300, deadline=None)
@given(json_values, json_values)
def test_diff_applies_for_arbitrary_json(a: Any, b: Any) -> None:
    assert apply(a, diff(a, b)) == b


id_items = st.lists(
    st.tuples(st.sampled_from([f"r{i}" for i in range(8)]), st.text(max_size=2)),
    max_size=7,
    unique_by=lambda t: t[0],
).map(lambda items: [{"id": i, "text": t} for i, t in items])


@settings(max_examples=300, deadline=None)
@given(id_items, id_items)
def test_diff_applies_for_id_lists(a: list[dict[str, str]], b: list[dict[str, str]]) -> None:
    da, db = {"rows": a}, {"rows": b}
    assert apply(da, diff(da, db)) == db


words = st.text(alphabet="abcdefgh$1234567890.%", min_size=1, max_size=6)


@settings(max_examples=150, deadline=None)
@given(
    st.lists(st.lists(words, min_size=3, max_size=3), min_size=1, max_size=8, unique_by=lambda r: r[0]),
    st.lists(st.lists(words, min_size=3, max_size=3), min_size=1, max_size=8, unique_by=lambda r: r[0]),
)
def test_aligned_sheet_diff_roundtrips(rows_a: list[list[str]], rows_b: list[list[str]]) -> None:
    minter = IdMinter()
    headers = ["Account", "Owner", "Q3 revenue"]
    first = align(None, candidate_sheet(headers, rows_a), minter).doc
    second = align(first, candidate_sheet(headers, rows_b), minter).doc
    a, b = first.model_dump(mode="json"), second.model_dump(mode="json")
    assert apply(a, diff(a, b)) == b


@settings(max_examples=150, deadline=None)
@given(st.lists(words, min_size=1, max_size=10))
def test_noop_version_keeps_every_id(lines: list[str]) -> None:
    minter = IdMinter()
    first = align(None, candidate_code(lines), minter).doc
    again = align(first, candidate_code(lines), minter)
    assert again.changes == []
    assert [ln.id for ln in again.doc.code.lines] == [ln.id for ln in first.code.lines]  # type: ignore[union-attr]
    a, b = first.model_dump(mode="json"), again.doc.model_dump(mode="json")
    assert [o for o in diff(a, b) if o.path != "/version"] == []


@settings(max_examples=150, deadline=None)
@given(st.lists(st.lists(words, min_size=3, max_size=3), min_size=1, max_size=8, unique_by=lambda r: r[0]))
def test_noop_sheet_version_keeps_every_id(rows: list[list[str]]) -> None:
    minter = IdMinter()
    headers = ["Account", "Owner", "Q3 revenue"]
    first = align(None, candidate_sheet(headers, rows), minter).doc
    again = align(first, candidate_sheet(headers, rows), minter)
    assert again.changes == []
    assert again.doc.sheet == first.sheet
