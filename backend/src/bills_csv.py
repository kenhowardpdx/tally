from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import date

from pydantic import ValidationError

from src.forecast.bill import validate_recurrence_config
from src.models.bill import Bill, RecurrenceType
from src.schemas.bill import BillCreate

CSV_COLUMNS = [
    "name",
    "amount",
    "recurrence_type",
    "semimonthly_days",
    "custom_interval_days",
    "start_date",
    "end_date",
    "enabled",
    "notes",
]


@dataclass
class RowError:
    row: int  # 1-indexed, counting the header as row 1 (so row 2 is the first data row)
    message: str


def bill_to_csv_row(bill: Bill) -> dict:
    """A Bill ORM instance -> a human-readable CSV row (dollars, not cents;
    semimonthly/custom_days config flattened into their own columns instead
    of raw JSON, since spreadsheet users shouldn't need to hand-edit JSON)."""
    semimonthly_days = ""
    custom_interval_days = ""
    if bill.recurrence_type == RecurrenceType.SEMIMONTHLY:
        semimonthly_days = ",".join(str(d) for d in bill.recurrence_config.get("days", []))
    elif bill.recurrence_type == RecurrenceType.CUSTOM_DAYS:
        interval = bill.recurrence_config.get("interval_days")
        custom_interval_days = str(interval) if interval is not None else ""

    return {
        "name": bill.name,
        "amount": f"{bill.amount_cents / 100:.2f}",
        "recurrence_type": bill.recurrence_type.value,
        "semimonthly_days": semimonthly_days,
        "custom_interval_days": custom_interval_days,
        "start_date": bill.start_date.isoformat(),
        "end_date": bill.end_date.isoformat() if bill.end_date else "",
        "enabled": "true" if bill.enabled else "false",
        "notes": bill.notes or "",
    }


def bills_to_csv(bills: list) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS)
    writer.writeheader()
    for bill in bills:
        writer.writerow(bill_to_csv_row(bill))
    return buffer.getvalue()


def _parse_amount_cents(raw: str) -> int:
    return round(float(raw) * 100)


def _field(row: dict, key: str) -> str:
    # csv.DictReader sets missing trailing fields to None (restval), not an
    # absent key - row.get(key, "") only covers a truly absent key, so a
    # short row would otherwise hit `.strip()` on None and raise
    # AttributeError instead of a clean per-row ValueError.
    return (row.get(key) or "").strip()


def _parse_recurrence_config(row: dict, recurrence_type: RecurrenceType) -> dict:
    # Only builds the dict from the CSV's flattened columns - validate_recurrence_config
    # (backend/src/forecast/bill.py, the single source of truth for these shapes) is what
    # actually checks it, so this and the JSON create/update API path can't drift apart.
    if recurrence_type == RecurrenceType.SEMIMONTHLY:
        days_raw = _field(row, "semimonthly_days")
        try:
            days = [int(d.strip()) for d in days_raw.split(",") if d.strip()]
        except ValueError as exc:
            raise ValueError('semimonthly_days must be integers, e.g. "10,25"') from exc
        recurrence_config: dict = {"days": days}
    elif recurrence_type == RecurrenceType.CUSTOM_DAYS:
        interval_raw = _field(row, "custom_interval_days")
        try:
            interval = int(interval_raw) if interval_raw else None
        except ValueError as exc:
            raise ValueError("custom_interval_days must be an integer") from exc
        recurrence_config = {"interval_days": interval} if interval is not None else {}
    else:
        recurrence_config = {}

    reason = validate_recurrence_config(recurrence_type, recurrence_config)
    if reason:
        raise ValueError(reason)
    return recurrence_config


def _parse_row(row: dict) -> BillCreate:
    name = _field(row, "name")
    if not name:
        raise ValueError("name is required")

    amount_raw = _field(row, "amount")
    if not amount_raw:
        raise ValueError("amount is required")
    amount_cents = _parse_amount_cents(amount_raw)

    recurrence_type_raw = _field(row, "recurrence_type")
    try:
        recurrence_type = RecurrenceType(recurrence_type_raw)
    except ValueError as exc:
        valid = ", ".join(t.value for t in RecurrenceType)
        raise ValueError(f"recurrence_type must be one of: {valid}") from exc

    recurrence_config = _parse_recurrence_config(row, recurrence_type)

    start_date_raw = _field(row, "start_date")
    if not start_date_raw:
        raise ValueError("start_date is required")
    start_date = date.fromisoformat(start_date_raw)

    end_date_raw = _field(row, "end_date")
    end_date = date.fromisoformat(end_date_raw) if end_date_raw else None

    enabled_raw = _field(row, "enabled").lower()
    enabled = enabled_raw not in ("false", "0")

    notes = _field(row, "notes") or None

    return BillCreate(
        name=name,
        amount_cents=amount_cents,
        recurrence_type=recurrence_type,
        recurrence_config=recurrence_config,
        start_date=start_date,
        end_date=end_date,
        enabled=enabled,
        notes=notes,
    )


def parse_csv_rows(csv_text: str) -> tuple[list[BillCreate], list[RowError]]:
    """All-or-nothing: every row is validated before any is returned as
    importable. If `errors` is non-empty, `bills` should not be inserted."""
    reader = csv.DictReader(io.StringIO(csv_text))
    bills: list[BillCreate] = []
    errors: list[RowError] = []

    for row_number, row in enumerate(reader, start=2):  # row 1 is the header
        try:
            bills.append(_parse_row(row))
        except (ValueError, TypeError, ValidationError) as exc:
            errors.append(RowError(row=row_number, message=str(exc)))

    return bills, errors
