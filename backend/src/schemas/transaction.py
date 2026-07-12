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


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    bill_id: int | None
    amount_cents: int
    date: date_
    description: str | None
    created_at: datetime
