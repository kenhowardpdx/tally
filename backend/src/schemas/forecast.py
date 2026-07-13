from datetime import date

from pydantic import BaseModel, field_validator

from src.models.bank_account import CycleType


class ForecastRequest(BaseModel):
    start_date: date
    end_date: date
    starting_balance_cents: int
    income_per_cycle_cents: int
    cycle_type: CycleType

    @field_validator("end_date")
    @classmethod
    def _end_on_or_after_start(cls, end_date: date, info) -> date:
        start_date = info.data.get("start_date")
        if start_date and end_date < start_date:
            raise ValueError("end_date must be on or after start_date")
        return end_date


class ForecastBillLine(BaseModel):
    bill_id: int
    name: str
    amount_cents: int
    forecasted_amount_cents: int
    due_date: date
    completed: bool
    notes: str | None


class ForecastTransactionLine(BaseModel):
    transaction_id: int
    amount_cents: int
    date: date
    description: str | None


class ForecastWindfallLine(BaseModel):
    windfall_id: int
    name: str
    amount_cents: int
    forecasted_amount_cents: int
    expected_date: date
    completed: bool
    notes: str | None


class ForecastCycle(BaseModel):
    start_date: date
    end_date: date
    bills: list[ForecastBillLine]
    transactions: list[ForecastTransactionLine]
    windfalls: list[ForecastWindfallLine]
    net_cents: int
    running_balance_cents: int


class UnscheduledBill(BaseModel):
    bill_id: int
    name: str
    reason: str


class ForecastResponse(BaseModel):
    cycles: list[ForecastCycle]
    starting_balance_cents: int
    ending_balance_cents: int
    unscheduled_bills: list[UnscheduledBill]
