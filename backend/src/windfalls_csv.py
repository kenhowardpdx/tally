from __future__ import annotations

import csv
import io
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from pydantic import ValidationError

from src.csv_match import ReconcileResult, reconcile
from src.models.windfall import Windfall
from src.schemas.windfall import WindfallCreate

CSV_COLUMNS = ["name", "amount", "expected_date", "enabled"]

# name/amount_cents/expected_date are the match key itself (see
# _windfall_key) - enabled is the only field left over to diff, so a matched
# windfall row only ever changes via being (re-)enabled/disabled, never a
# genuine field edit. That's expected: Windfall has no other mutable fields.
WINDFALL_DIFF_FIELDS = ["enabled"]


@dataclass
class RowError:
    row: int  # 1-indexed, counting the header as row 1 (so row 2 is the first data row)
    message: str


def windfall_to_csv_row(windfall: Windfall) -> dict:
    return {
        "name": windfall.name,
        "amount": f"{windfall.amount_cents / 100:.2f}",
        "expected_date": windfall.expected_date.isoformat(),
        "enabled": "true" if windfall.enabled else "false",
    }


def windfalls_to_csv(windfalls: list[Windfall]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS)
    writer.writeheader()
    for windfall in windfalls:
        writer.writerow(windfall_to_csv_row(windfall))
    return buffer.getvalue()


def _parse_amount_cents(raw: str) -> int:
    return round(float(raw) * 100)


def _field(row: dict, key: str) -> str:
    # csv.DictReader sets missing trailing fields to None (restval), not an
    # absent key - row.get(key, "") only covers a truly absent key, so a
    # short row would otherwise hit `.strip()` on None and raise
    # AttributeError instead of a clean per-row ValueError.
    return (row.get(key) or "").strip()


def _parse_row(row: dict) -> WindfallCreate:
    name = _field(row, "name")
    if not name:
        raise ValueError("name is required")

    amount_raw = _field(row, "amount")
    if not amount_raw:
        raise ValueError("amount is required")
    amount_cents = _parse_amount_cents(amount_raw)
    if amount_cents <= 0:
        raise ValueError("amount must be greater than zero")

    expected_date_raw = _field(row, "expected_date")
    if not expected_date_raw:
        raise ValueError("expected_date is required")
    expected_date = date.fromisoformat(expected_date_raw)

    enabled_raw = _field(row, "enabled").lower()
    enabled = enabled_raw not in ("false", "0")

    return WindfallCreate(
        name=name, amount_cents=amount_cents, expected_date=expected_date, enabled=enabled
    )


def parse_csv_rows(csv_text: str) -> tuple[list[WindfallCreate], list[RowError]]:
    """All-or-nothing: every row is validated before any is returned as
    importable. If `errors` is non-empty, `windfalls` should not be inserted."""
    reader = csv.DictReader(io.StringIO(csv_text))
    windfalls: list[WindfallCreate] = []
    errors: list[RowError] = []

    for row_number, row in enumerate(reader, start=2):  # row 1 is the header
        try:
            windfalls.append(_parse_row(row))
        except (ValueError, TypeError, ValidationError) as exc:
            errors.append(RowError(row=row_number, message=str(exc)))

    return windfalls, errors


def _windfall_key(row: Windfall | WindfallCreate) -> tuple:
    return (row.name.strip().lower(), row.amount_cents, row.expected_date)


def reconcile_windfalls(
    existing: Sequence[Windfall], parsed: Sequence[WindfallCreate]
) -> ReconcileResult[Windfall, WindfallCreate]:
    return reconcile(existing, parsed, key_fn=_windfall_key, diff_fields=WINDFALL_DIFF_FIELDS)
