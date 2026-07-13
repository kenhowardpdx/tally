from datetime import date

from pydantic import BaseModel


class BillHistoryEntry(BaseModel):
    cycle_start_date: date
    cycle_end_date: date
    due_date: date
    expected_amount_cents: int
    actual_amount_cents: int
    completed: bool
    notes: str | None
    variance_cents: int


class BillHistoryResponse(BaseModel):
    bill_id: int
    total: int
    entries: list[BillHistoryEntry]
