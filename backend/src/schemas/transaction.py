from datetime import date as date_
from datetime import datetime

from pydantic import BaseModel, ConfigDict

# The Transaction model's date column is named `date`, matching the field
# name below - so `date` is imported under an alias (`date_`) to avoid a
# real Python gotcha: `date: date | None = None` self-shadows, since the
# default value (None) gets bound to the name `date` in the class body
# *before* the `date | None` annotation expression is evaluated, and that
# corrupted local persists even under `from __future__ import annotations`
# (Pydantic's forward-ref resolution consults the class's own namespace).


class TransactionCreate(BaseModel):
    # Signed: positive credits the balance, negative debits it - unlike Bill
    # (always a positive expense) a transaction is general-purpose.
    amount_cents: int
    date: date_
    description: str | None = None
    bill_id: int | None = None


class TransactionUpdate(BaseModel):
    amount_cents: int | None = None
    date: date_ | None = None
    description: str | None = None
    bill_id: int | None = None
    account_id: int | None = None


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    bill_id: int | None
    amount_cents: int
    date: date_
    description: str | None
    created_at: datetime


class TransactionImportRowIssue(BaseModel):
    row: int
    message: str


class TransactionImportAmbiguous(BaseModel):
    # No row number - describes a match collision found during
    # reconciliation, not a single malformed CSV row.
    message: str


class TransactionImportUpdate(BaseModel):
    id: int
    fields: TransactionCreate


class TransactionImportPreview(BaseModel):
    new: list[TransactionCreate]
    updated: list[TransactionImportUpdate]
    unchanged_count: int
    ambiguous: list[TransactionImportAmbiguous]
    # Existing transactions that will be *permanently deleted* if this
    # preview is committed - unlike Bills/Windfalls, Transaction has no
    # soft-delete flag and nothing references transactions.id, so omission
    # here means a real, irreversible DELETE.
    omitted: list[TransactionRead]
    # bill_name didn't resolve to exactly one bill on this account - the row
    # still imports, just unlinked (bill_id null).
    warnings: list[TransactionImportRowIssue]
    errors: list[TransactionImportRowIssue]


class TransactionImportCommitRequest(BaseModel):
    new: list[TransactionCreate]
    updated: list[TransactionImportUpdate]
    omitted_ids: list[int]


class TransactionImportCommitResponse(BaseModel):
    created: list[TransactionRead]
    updated: list[TransactionRead]
    deleted_count: int
