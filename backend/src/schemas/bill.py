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
