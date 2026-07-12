from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from src.models.bank_account import CycleType


class BankAccountCreate(BaseModel):
    name: str
    institution: str | None = None


class BankAccountUpdate(BaseModel):
    name: str | None = None
    institution: str | None = None


class BankAccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    institution: str | None
    created_at: datetime
    # Last-used forecast settings (null until a forecast has been run for this
    # account at least once) - see schemas/forecast.py's ForecastRequest.
    forecast_starting_balance_cents: int | None
    forecast_income_per_cycle_cents: int | None
    forecast_cycle_type: CycleType | None
    forecast_start_date: date | None
    forecast_end_date: date | None
