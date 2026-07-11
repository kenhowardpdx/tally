from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from src.models.bill import RecurrenceType


class BillCreate(BaseModel):
    name: str
    amount_cents: int
    recurrence_type: RecurrenceType
    recurrence_config: dict = {}
    start_date: date
    end_date: date | None = None
    enabled: bool = True


class BillUpdate(BaseModel):
    name: str | None = None
    amount_cents: int | None = None
    recurrence_type: RecurrenceType | None = None
    recurrence_config: dict | None = None
    start_date: date | None = None
    end_date: date | None = None
    enabled: bool | None = None
    account_id: int | None = None


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
    created_at: datetime
    updated_at: datetime
