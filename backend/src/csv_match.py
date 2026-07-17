from __future__ import annotations

from collections.abc import Callable, Hashable, Sequence
from dataclasses import dataclass


@dataclass
class Updated[Existing, Parsed]:
    existing: Existing
    parsed: Parsed


@dataclass
class Ambiguous[Parsed]:
    parsed: Parsed
    matches: list  # the >1 existing rows this row's key collided with


@dataclass
class ReconcileResult[Existing, Parsed]:
    new: list[Parsed]
    updated: list[Updated[Existing, Parsed]]
    unchanged: list[Existing]
    ambiguous: list[Ambiguous[Parsed]]
    # Existing rows whose key never appeared in any parsed CSV row. Callers
    # that have a soft-delete concept (Bill.enabled, Windfall.enabled) should
    # filter this to already-enabled rows before acting on it - an
    # already-disabled row reappearing here would just be a no-op re-disable.
    omitted: list[Existing]


def reconcile[Existing, Parsed](
    existing_rows: Sequence[Existing],
    parsed_rows: Sequence[Parsed],
    key_fn: Callable[[Existing | Parsed], Hashable],
    diff_fields: Sequence[str],
) -> ReconcileResult[Existing, Parsed]:
    """Buckets each parsed CSV row against an account's current rows by a
    fuzzy field-match key (`key_fn`) - there's no id column round-tripped
    through the CSV, so "is this row the same as that one" is inferred
    entirely from field values. `diff_fields` are compared via getattr to
    decide "updated" vs "unchanged" once a row's key resolves to exactly one
    existing row.

    A CSV with two rows that key to the same value (e.g. a duplicated line)
    will each independently match the same existing row - harmless (the
    second update is a redundant no-op), not guarded against here.
    """
    by_key: dict[Hashable, list[Existing]] = {}
    for row in existing_rows:
        by_key.setdefault(key_fn(row), []).append(row)

    matched_keys: set[Hashable] = set()
    new: list[Parsed] = []
    updated: list[Updated[Existing, Parsed]] = []
    unchanged: list[Existing] = []
    ambiguous: list[Ambiguous[Parsed]] = []

    for parsed in parsed_rows:
        key = key_fn(parsed)
        matches = by_key.get(key, [])
        if not matches:
            new.append(parsed)
            continue

        matched_keys.add(key)
        if len(matches) > 1:
            ambiguous.append(Ambiguous(parsed=parsed, matches=matches))
            continue

        existing = matches[0]
        if any(getattr(existing, field) != getattr(parsed, field) for field in diff_fields):
            updated.append(Updated(existing=existing, parsed=parsed))
        else:
            unchanged.append(existing)

    omitted = [row for key, rows in by_key.items() if key not in matched_keys for row in rows]

    return ReconcileResult(
        new=new, updated=updated, unchanged=unchanged, ambiguous=ambiguous, omitted=omitted
    )
