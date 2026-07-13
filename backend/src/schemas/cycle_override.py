from datetime import date, datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

# Matches CycleOverride.notes' String(1000) column - keeps an over-long note
# a clean 422 at the schema layer instead of an unhandled DB error at commit
# time.
_NOTES_MAX_LENGTH = 1000


class CycleOverrideUpsert(BaseModel):
    account_id: int
    bill_id: int | None = None
    windfall_id: int | None = None
    cycle_start_date: date
    completed: bool = False
    override_amount_cents: int | None = None
    notes: str | None = Field(default=None, max_length=_NOTES_MAX_LENGTH)

    @model_validator(mode="after")
    def _exactly_one_target(self) -> Self:
        if (self.bill_id is None) == (self.windfall_id is None):
            raise ValueError("Exactly one of bill_id or windfall_id must be set")
        return self


class CycleOverrideRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    bill_id: int | None
    windfall_id: int | None
    cycle_start_date: date
    completed: bool
    override_amount_cents: int | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
