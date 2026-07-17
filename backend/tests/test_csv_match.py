from dataclasses import dataclass

from src.csv_match import reconcile


@dataclass
class _Existing:
    id: int
    key: str
    value: int


@dataclass
class _Parsed:
    key: str
    value: int


def _key(row: _Existing | _Parsed) -> str:
    return row.key


def test_row_with_no_matching_key_is_new():
    result = reconcile([], [_Parsed(key="a", value=1)], key_fn=_key, diff_fields=["value"])
    assert result.new == [_Parsed(key="a", value=1)]
    assert result.updated == []
    assert result.unchanged == []
    assert result.ambiguous == []
    assert result.omitted == []


def test_matching_row_with_identical_diff_fields_is_unchanged():
    existing = _Existing(id=1, key="a", value=1)
    result = reconcile([existing], [_Parsed(key="a", value=1)], key_fn=_key, diff_fields=["value"])
    assert result.new == []
    assert result.updated == []
    assert result.unchanged == [existing]
    assert result.omitted == []


def test_matching_row_with_different_diff_field_is_updated():
    existing = _Existing(id=1, key="a", value=1)
    parsed = _Parsed(key="a", value=2)
    result = reconcile([existing], [parsed], key_fn=_key, diff_fields=["value"])
    assert result.new == []
    assert result.unchanged == []
    assert len(result.updated) == 1
    assert result.updated[0].existing is existing
    assert result.updated[0].parsed is parsed


def test_key_matching_multiple_existing_rows_is_ambiguous():
    dup_a = _Existing(id=1, key="a", value=1)
    dup_b = _Existing(id=2, key="a", value=1)
    parsed = _Parsed(key="a", value=1)
    result = reconcile([dup_a, dup_b], [parsed], key_fn=_key, diff_fields=["value"])
    assert result.new == []
    assert result.updated == []
    assert result.unchanged == []
    assert len(result.ambiguous) == 1
    assert result.ambiguous[0].parsed is parsed
    assert result.ambiguous[0].matches == [dup_a, dup_b]
    # An ambiguous existing row isn't also reported as omitted - its key did
    # appear in the CSV, just too many times to resolve automatically.
    assert result.omitted == []


def test_existing_row_absent_from_any_parsed_row_is_omitted():
    existing = _Existing(id=1, key="a", value=1)
    result = reconcile([existing], [], key_fn=_key, diff_fields=["value"])
    assert result.new == []
    assert result.updated == []
    assert result.unchanged == []
    assert result.ambiguous == []
    assert result.omitted == [existing]


def test_omitted_and_matched_rows_coexist_correctly():
    kept = _Existing(id=1, key="a", value=1)
    dropped = _Existing(id=2, key="b", value=1)
    result = reconcile([kept, dropped], [_Parsed(key="a", value=1)], key_fn=_key, diff_fields=["value"])
    assert result.unchanged == [kept]
    assert result.omitted == [dropped]
