from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_db_user
from src.core.database import get_db
from src.forecast import (
    ForecastBill,
    ForecastCycleOverride,
    ForecastTransaction,
    ForecastWindfall,
    find_current_cycle_bounds,
    get_forecast,
    iter_cycle_bounds,
)
from src.models import BankAccount, Bill, CycleOverride, Transaction, User, Windfall
from src.schemas.dashboard import DashboardAccountSummary, DashboardResponse
from src.schemas.forecast import ForecastBillLine, ForecastTransactionLine, ForecastWindfallLine

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


async def _current_cycle_summary(db: AsyncSession, account: BankAccount, today: date) -> DashboardAccountSummary:
    base = {
        "account_id": account.id,
        "account_name": account.name,
        "institution": account.institution,
    }

    if account.forecast_start_date is None or account.forecast_cycle_type is None:
        return DashboardAccountSummary(**base, configured=False)

    anchor = account.forecast_start_date
    cycle_type = account.forecast_cycle_type
    is_upcoming = today < anchor
    if is_upcoming:
        # No prior cycle has run yet - the best available snapshot is the
        # first cycle the account's saved settings will generate.
        cycle_start, cycle_end = next(iter_cycle_bounds(cycle_type, anchor, anchor))
    else:
        cycle_start, cycle_end = find_current_cycle_bounds(cycle_type, anchor, today)

    bills_result = await db.execute(
        select(Bill).where(Bill.account_id == account.id, Bill.enabled.is_(True))
    )
    forecast_bills = [
        ForecastBill(
            id=bill.id,
            name=bill.name,
            amount_cents=bill.amount_cents,
            recurrence_type=bill.recurrence_type,
            recurrence_config=bill.recurrence_config,
            start_date=bill.start_date,
            end_date=bill.end_date,
        )
        for bill in bills_result.scalars().all()
    ]

    # anchor..cycle_end exactly bounds the cycles get_forecast() below will
    # generate (cycle_end is the target cycle's real end, not a caller-chosen
    # cutoff that a cycle could run past - see find_current_cycle_bounds), so
    # this is a precise query window, not an over-fetch.
    transactions_result = await db.execute(
        select(Transaction).where(
            Transaction.account_id == account.id,
            Transaction.date >= anchor,
            Transaction.date <= cycle_end,
        )
    )
    forecast_transactions = [
        ForecastTransaction(
            id=transaction.id,
            amount_cents=transaction.amount_cents,
            date=transaction.date,
            description=transaction.description,
        )
        for transaction in transactions_result.scalars().all()
    ]

    windfalls_result = await db.execute(
        select(Windfall).where(
            Windfall.account_id == account.id,
            Windfall.expected_date >= anchor,
            Windfall.expected_date <= cycle_end,
        )
    )
    forecast_windfalls = [
        ForecastWindfall(
            id=windfall.id,
            name=windfall.name,
            amount_cents=windfall.amount_cents,
            expected_date=windfall.expected_date,
        )
        for windfall in windfalls_result.scalars().all()
    ]

    overrides_result = await db.execute(
        select(CycleOverride).where(
            CycleOverride.account_id == account.id,
            CycleOverride.cycle_start_date >= anchor,
            CycleOverride.cycle_start_date <= cycle_end,
        )
    )
    forecast_overrides = [
        ForecastCycleOverride(
            bill_id=override.bill_id,
            windfall_id=override.windfall_id,
            cycle_start_date=override.cycle_start_date,
            completed=override.completed,
            override_amount_cents=override.override_amount_cents,
            notes=override.notes,
        )
        for override in overrides_result.scalars().all()
    ]

    forecast = get_forecast(
        forecast_bills,
        cycle_type,
        anchor,
        cycle_end,
        account.forecast_starting_balance_cents or 0,
        account.forecast_income_per_cycle_cents or 0,
        transactions=forecast_transactions,
        windfalls=forecast_windfalls,
        overrides=forecast_overrides,
    )
    # anchor <= cycle_start by construction, and next_start always exceeds
    # cycle_end (see _cycle_bounds/find_current_cycle_bounds), so the target
    # cycle is always the last one get_forecast() generates in this window.
    current_cycle = forecast.cycles[-1]
    starting_balance_cents = (
        forecast.cycles[-2].running_balance_cents
        if len(forecast.cycles) >= 2
        else forecast.starting_balance_cents
    )

    return DashboardAccountSummary(
        **base,
        configured=True,
        cycle_type=cycle_type,
        cycle_start_date=current_cycle.start_date,
        cycle_end_date=current_cycle.end_date,
        is_upcoming=is_upcoming,
        starting_balance_cents=starting_balance_cents,
        ending_balance_cents=current_cycle.running_balance_cents,
        bills=[
            ForecastBillLine(
                bill_id=line.bill_id,
                name=line.name,
                amount_cents=line.amount_cents,
                forecasted_amount_cents=line.forecasted_amount_cents,
                due_date=line.due_date,
                completed=line.completed,
                notes=line.notes,
            )
            for line in current_cycle.bills
        ],
        transactions=[
            ForecastTransactionLine(
                transaction_id=line.transaction_id,
                amount_cents=line.amount_cents,
                date=line.date,
                description=line.description,
            )
            for line in current_cycle.transactions
        ],
        windfalls=[
            ForecastWindfallLine(
                windfall_id=line.windfall_id,
                name=line.name,
                amount_cents=line.amount_cents,
                forecasted_amount_cents=line.forecasted_amount_cents,
                expected_date=line.expected_date,
                completed=line.completed,
                notes=line.notes,
            )
            for line in current_cycle.windfalls
        ],
        net_cents=current_cycle.net_cents,
    )


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_db_user),
) -> DashboardResponse:
    accounts_result = await db.execute(
        select(BankAccount).where(BankAccount.user_id == current_user.id).order_by(BankAccount.id)
    )
    accounts = list(accounts_result.scalars().all())

    today = date.today()
    summaries = [await _current_cycle_summary(db, account, today) for account in accounts]

    combined_ending_balance_cents = sum(
        summary.ending_balance_cents for summary in summaries if summary.configured
    )

    return DashboardResponse(
        accounts=summaries,
        combined_ending_balance_cents=combined_ending_balance_cents,
    )
