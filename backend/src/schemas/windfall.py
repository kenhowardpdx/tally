from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class WindfallCreate(BaseModel):
    name: str
    # Always positive - a windfall is income by definition.
    amount_cents: int
    expected_date: date


class WindfallUpdate(BaseModel):
    name: str | None = None
    amount_cents: int | None = None
    expected_date: date | None = None


class WindfallRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    name: str
    amount_cents: int
    expected_date: date
    created_at: datetime
