from fastapi import APIRouter

from src.forecast import ForecastBill, get_forecast
from src.schemas.demo import DemoForecastRequest
from src.schemas.forecast import ForecastBillLine, ForecastCycle, ForecastResponse, UnscheduledBill

router = APIRouter(prefix="/api/v1/demo", tags=["demo"])


@router.post("/forecast", response_model=ForecastResponse)
async def compute_demo_forecast(payload: DemoForecastRequest) -> ForecastResponse:
    """Unauthenticated forecast preview for the logged-out marketing homepage.

    No account, no auth, no database access - runs the same get_forecast()
    the real product uses directly against bills supplied in the request, so
    the demo's math is guaranteed identical to a signed-in user's forecast
    rather than a separate JS reimplementation that could quietly drift.
    """
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
        for bill in payload.bills
    ]

    forecast = get_forecast(
        forecast_bills,
        payload.cycle_type,
        payload.start_date,
        payload.end_date,
        payload.starting_balance_cents,
        payload.income_per_cycle_cents,
    )

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
                        forecasted_amount_cents=line.forecasted_amount_cents,
                        due_date=line.due_date,
                        completed=line.completed,
                        notes=line.notes,
                    )
                    for line in cycle.bills
                ],
                transactions=[],
                windfalls=[],
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
