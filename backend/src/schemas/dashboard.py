from datetime import date

from pydantic import BaseModel

from src.models.bank_account import CycleType
from src.schemas.forecast import ForecastBillLine, ForecastTransactionLine, ForecastWindfallLine


class DashboardAccountSummary(BaseModel):
    account_id: int
    account_name: str
    institution: str | None
    # False if the account has never had a forecast run (no forecast_start_date
    # saved yet) - nothing below is meaningful in that case.
    configured: bool
    cycle_type: CycleType | None = None
    cycle_start_date: date | None = None
    cycle_end_date: date | None = None
    # True if today is before the account's forecast_start_date, so this is
    # the first upcoming cycle rather than one actually in progress - there's
    # no prior cycle to have carried a running balance from.
    is_upcoming: bool = False
    starting_balance_cents: int | None = None
    ending_balance_cents: int | None = None
    bills: list[ForecastBillLine] = []
    transactions: list[ForecastTransactionLine] = []
    windfalls: list[ForecastWindfallLine] = []
    net_cents: int | None = None


class DashboardResponse(BaseModel):
    accounts: list[DashboardAccountSummary]
    # Sum of ending_balance_cents across configured accounts only - accounts
    # that have never run a forecast don't contribute (nothing to sum).
    combined_ending_balance_cents: int
