from datetime import date

from pydantic import BaseModel, field_validator

from src.forecast.bill import validate_recurrence_config
from src.models.bank_account import CycleType
from src.models.bill import RecurrenceType


class DemoBill(BaseModel):
    # Client-assigned within a single demo request (e.g. array index) -
    # there's no database row behind a demo bill, so these only need to be
    # unique within the request, not globally.
    id: int
    name: str
    amount_cents: int
    recurrence_type: RecurrenceType
    recurrence_config: dict = {}
    start_date: date
    end_date: date | None = None

    @field_validator("recurrence_config")
    @classmethod
    def _valid_for_recurrence_type(cls, recurrence_config: dict, info) -> dict:
        recurrence_type = info.data.get("recurrence_type")
        if recurrence_type is not None:
            reason = validate_recurrence_config(recurrence_type, recurrence_config)
            if reason:
                raise ValueError(reason)
        return recurrence_config


class DemoForecastRequest(BaseModel):
    bills: list[DemoBill]
    cycle_type: CycleType
    start_date: date
    end_date: date
    starting_balance_cents: int
    income_per_cycle_cents: int

    @field_validator("end_date")
    @classmethod
    def _end_on_or_after_start(cls, end_date: date, info) -> date:
        start_date = info.data.get("start_date")
        if start_date and end_date < start_date:
            raise ValueError("end_date must be on or after start_date")
        # Same unauthenticated-endpoint reasoning as the bill count cap below:
        # bound the number of cycles a single request can force the engine
        # to compute.
        if start_date and (end_date - start_date).days > 366:
            raise ValueError("demo forecasts are limited to a 366-day window")
        return end_date

    @field_validator("bills")
    @classmethod
    def _cap_bill_count(cls, bills: list[DemoBill]) -> list[DemoBill]:
        # The demo is a public, unauthenticated endpoint with no rate limiting
        # of its own - a small cap keeps a single request's forecast
        # computation bounded regardless of what a visitor (or a script)
        # sends.
        if len(bills) > 25:
            raise ValueError("demo forecasts are limited to 25 bills")
        return bills
