from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_owned_bank_account
from src.core.database import get_db
from src.forecast import ForecastBill, ForecastTransaction, ForecastWindfall, get_forecast
from src.models import BankAccount, Bill, Transaction, Windfall
from src.schemas.forecast import (
    ForecastBillLine,
    ForecastCycle,
    ForecastRequest,
    ForecastResponse,
    ForecastTransactionLine,
    ForecastWindfallLine,
    UnscheduledBill,
)

router = APIRouter(prefix="/api/v1/accounts/{account_id}/forecast", tags=["forecast"])


@router.post("", response_model=ForecastResponse)
async def compute_forecast(
    payload: ForecastRequest,
    db: AsyncSession = Depends(get_db),
    account: BankAccount = Depends(get_owned_bank_account),
) -> ForecastResponse:
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

    transactions_result = await db.execute(
        select(Transaction).where(Transaction.account_id == account.id)
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

    windfalls_result = await db.execute(select(Windfall).where(Windfall.account_id == account.id))
    forecast_windfalls = [
        ForecastWindfall(
            id=windfall.id,
            name=windfall.name,
            amount_cents=windfall.amount_cents,
            expected_date=windfall.expected_date,
        )
        for windfall in windfalls_result.scalars().all()
    ]

    forecast = get_forecast(
        forecast_bills,
        payload.cycle_type,
        payload.start_date,
        payload.end_date,
        payload.starting_balance_cents,
        payload.income_per_cycle_cents,
        transactions=forecast_transactions,
        windfalls=forecast_windfalls,
    )

    # Persist as the account's last-used forecast settings (side effect of an
    # otherwise read-only computation) so GET .../accounts/{id} reflects what
    # was just run - revisiting the forecast page prefills the form with it
    # instead of the user re-entering the same starting balance/dates every
    # ~2-week pay cycle.
    account.forecast_starting_balance_cents = payload.starting_balance_cents
    account.forecast_income_per_cycle_cents = payload.income_per_cycle_cents
    account.forecast_cycle_type = payload.cycle_type
    account.forecast_start_date = payload.start_date
    account.forecast_end_date = payload.end_date
    await db.commit()

    return ForecastResponse(
        cycles=[
            ForecastCycle(
                start_date=cycle.start_date,
                end_date=cycle.end_date,
                bills=[
                    ForecastBillLine(
                        bill_id=line.bill_id,
                        name=line.name,
                        amount_cents=line.amount_cents,
                        due_date=line.due_date,
                    )
                    for line in cycle.bills
                ],
                transactions=[
                    ForecastTransactionLine(
                        transaction_id=line.transaction_id,
                        amount_cents=line.amount_cents,
                        date=line.date,
                        description=line.description,
                    )
                    for line in cycle.transactions
                ],
                windfalls=[
                    ForecastWindfallLine(
                        windfall_id=line.windfall_id,
                        name=line.name,
                        amount_cents=line.amount_cents,
                        expected_date=line.expected_date,
                    )
                    for line in cycle.windfalls
                ],
                net_cents=cycle.net_cents,
                running_balance_cents=cycle.running_balance_cents,
            )
            for cycle in forecast.cycles
        ],
        starting_balance_cents=forecast.starting_balance_cents,
        ending_balance_cents=forecast.ending_balance_cents,
        unscheduled_bills=[
            UnscheduledBill(bill_id=bill.bill_id, name=bill.name, reason=bill.reason)
            for bill in forecast.unscheduled_bills
        ],
    )
