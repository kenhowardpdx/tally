from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from src.models.bill import RecurrenceType

# Matches Bill.notes' String(1000) column - keeps an over-long note a clean
# 422 at the schema layer instead of an unhandled DB error at commit time.
_NOTES_MAX_LENGTH = 1000


class BillCreate(BaseModel):
    name: str
    amount_cents: int
    recurrence_type: RecurrenceType
    recurrence_config: dict = {}
    start_date: date
    end_date: date | None = None
    enabled: bool = True
    notes: str | None = Field(default=None, max_length=_NOTES_MAX_LENGTH)


class BillUpdate(BaseModel):
    name: str | None = None
    amount_cents: int | None = None
    recurrence_type: RecurrenceType | None = None
    recurrence_config: dict | None = None
    start_date: date | None = None
    end_date: date | None = None
    enabled: bool | None = None
    account_id: int | None = None
    notes: str | None = Field(default=None, max_length=_NOTES_MAX_LENGTH)


class BillRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    name: str
    amount_cents: int
    recurrence_type: RecurrenceType
    recurrence_config: dict
    start_date: date
    end_date: date | None
    enabled: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime


class BillImportRowIssue(BaseModel):
    row: int
    message: str


class BillImportAmbiguous(BaseModel):
    # No row number - this describes a match collision found during
    # reconciliation (a CSV row's key matched more than one existing bill),
    # not a single malformed CSV row.
    message: str


class BillImportUpdate(BaseModel):
    id: int
    fields: BillCreate


class BillImportPreview(BaseModel):
    new: list[BillCreate]
    updated: list[BillImportUpdate]
    unchanged_count: int
    ambiguous: list[BillImportAmbiguous]
    # Currently-enabled bills that will be disabled (not deleted - see
    # bill_events/bill_history) if this preview is committed.
    omitted: list[BillRead]
    errors: list[BillImportRowIssue]


class BillImportCommitRequest(BaseModel):
    # Echoes the shape BillImportPreview returned - the client sends back
    # exactly what it wants applied, not the original CSV file.
    new: list[BillCreate]
    updated: list[BillImportUpdate]
    omitted_ids: list[int]


class BillImportCommitResponse(BaseModel):
    created: list[BillRead]
    updated: list[BillRead]
    disabled_count: int
