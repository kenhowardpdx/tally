from __future__ import annotations

import csv
import io
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from pydantic import ValidationError

from src.csv_match import ReconcileResult, reconcile
from src.models.bill import Bill
from src.models.transaction import Transaction
from src.schemas.transaction import TransactionCreate

CSV_COLUMNS = ["date", "amount", "description", "bill_name"]

# The only diffable field once a row's match key (date, amount_cents,
# description) resolves to exactly one existing transaction - those three
# key fields are effectively the whole entity already, so bill_id (the
# name-resolved link, see _resolve_bill_id) is the one thing reimporting can
# actually change.
TRANSACTION_DIFF_FIELDS = ["bill_id"]


@dataclass
class RowError:
    row: int  # 1-indexed, counting the header as row 1 (so row 2 is the first data row)
    message: str


@dataclass
class RowWarning:
    row: int
    message: str


def transaction_to_csv_row(transaction: Transaction, bill_name_by_id: dict[int, str]) -> dict:
    return {
        "date": transaction.date.isoformat(),
        "amount": f"{transaction.amount_cents / 100:.2f}",
        "description": transaction.description or "",
        "bill_name": bill_name_by_id.get(transaction.bill_id, "") if transaction.bill_id else "",
    }


def transactions_to_csv(transactions: list[Transaction], bills: Sequence[Bill]) -> str:
    bill_name_by_id = {bill.id: bill.name for bill in bills}
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS)
    writer.writeheader()
    for transaction in transactions:
        writer.writerow(transaction_to_csv_row(transaction, bill_name_by_id))
    return buffer.getvalue()


def _parse_amount_cents(raw: str) -> int:
    return round(float(raw) * 100)


def _field(row: dict, key: str) -> str:
    # csv.DictReader sets missing trailing fields to None (restval), not an
    # absent key - row.get(key, "") only covers a truly absent key, so a
    # short row would otherwise hit `.strip()` on None and raise
    # AttributeError instead of a clean per-row ValueError.
    return (row.get(key) or "").strip()


def _resolve_bill_id(bill_name: str, bills_by_name: dict[str, list[Bill]]) -> tuple[int | None, str | None]:
    """Returns (bill_id, warning) - bill_id is None whenever the name didn't
    resolve to exactly one bill on this account; the warning explains why so
    the row can still import (unlinked) instead of hard-failing."""
    if not bill_name:
        return None, None
    matches = bills_by_name.get(bill_name.lower(), [])
    if len(matches) == 1:
        return matches[0].id, None
    if len(matches) == 0:
        return None, f'No bill named "{bill_name}" - imported unlinked.'
    return None, f'Multiple bills named "{bill_name}" - imported unlinked.'


def _parse_row(
    row: dict, bills_by_name: dict[str, list[Bill]]
) -> tuple[TransactionCreate, str | None]:
    amount_raw = _field(row, "amount")
    if not amount_raw:
        raise ValueError("amount is required")
    amount_cents = _parse_amount_cents(amount_raw)

    date_raw = _field(row, "date")
    if not date_raw:
        raise ValueError("date is required")
    txn_date = date.fromisoformat(date_raw)

    description = _field(row, "description") or None
    bill_id, warning = _resolve_bill_id(_field(row, "bill_name"), bills_by_name)

    transaction = TransactionCreate(
        amount_cents=amount_cents, date=txn_date, description=description, bill_id=bill_id
    )
    return transaction, warning


def parse_csv_rows(
    csv_text: str, bills: Sequence[Bill]
) -> tuple[list[TransactionCreate], list[RowError], list[RowWarning]]:
    """All-or-nothing on hard errors: every row must parse before any is
    returned as importable. Ambiguous/missing bill-name links are soft
    warnings, not errors - the row still imports, just unlinked."""
    bills_by_name: dict[str, list[Bill]] = {}
    for bill in bills:
        bills_by_name.setdefault(bill.name.strip().lower(), []).append(bill)

    reader = csv.DictReader(io.StringIO(csv_text))
    transactions: list[TransactionCreate] = []
    errors: list[RowError] = []
    warnings: list[RowWarning] = []

    for row_number, row in enumerate(reader, start=2):  # row 1 is the header
        try:
            transaction, warning = _parse_row(row, bills_by_name)
        except (ValueError, TypeError, ValidationError) as exc:
            errors.append(RowError(row=row_number, message=str(exc)))
            continue
        transactions.append(transaction)
        if warning:
            warnings.append(RowWarning(row=row_number, message=warning))

    return transactions, errors, warnings


def _transaction_key(row: Transaction | TransactionCreate) -> tuple:
    return (row.date, row.amount_cents, row.description or "")


def reconcile_transactions(
    existing: Sequence[Transaction], parsed: Sequence[TransactionCreate]
) -> ReconcileResult[Transaction, TransactionCreate]:
    return reconcile(existing, parsed, key_fn=_transaction_key, diff_fields=TRANSACTION_DIFF_FIELDS)
