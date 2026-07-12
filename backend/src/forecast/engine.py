from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta

from src.forecast.bill import ForecastBill, validate_recurrence_config
from src.forecast.cycle import CycleBillLine, build_cycle
from src.models.bank_account import CycleType


@dataclass
class UnscheduledBill:
    bill_id: int
    name: str
    reason: str


@dataclass
class ForecastCycle:
    start_date: date
    end_date: date
    bills: list[CycleBillLine]
    cycle_sum_cents: int
    running_balance_cents: int


@dataclass
class ForecastResult:
    cycles: list[ForecastCycle]
    starting_balance_cents: int
    ending_balance_cents: int
    unscheduled_bills: list[UnscheduledBill]


def _last_day_of_month(year: int, month: int) -> int:
    return monthrange(year, month)[1]


def _add_months(d: date, months: int) -> date:
    total_month_index = d.month - 1 + months
    year = d.year + total_month_index // 12
    month = total_month_index % 12 + 1
    day = min(d.day, _last_day_of_month(year, month))
    return date(year, month, day)


def _normalize_semimonthly_start(start: date) -> date:
    """Snaps an arbitrary date to the actual boundary of the 10th/25th pay
    period it falls in: days 1-9 belong to the cycle that started the 25th of
    the *previous* month, 10-24 to the one starting the 10th, 25-31 to the one
    starting the 25th."""
    if start.day <= 9:
        prev_month = _add_months(date(start.year, start.month, 1), -1)
        return date(prev_month.year, prev_month.month, 25)
    if start.day <= 24:
        return date(start.year, start.month, 10)
    return date(start.year, start.month, 25)


def _cycle_bounds(cycle_type: CycleType, start: date) -> tuple[date, date]:
    """Given a cycle's (already-normalized) start date, returns
    (this cycle's end date, next cycle's start date)."""
    if cycle_type == CycleType.WEEKLY:
        return start + timedelta(days=6), start + timedelta(days=7)
    if cycle_type == CycleType.BIWEEKLY:
        return start + timedelta(days=13), start + timedelta(days=14)
    if cycle_type == CycleType.MONTHLY:
        next_start = _add_months(start, 1)
        return next_start - timedelta(days=1), next_start
    if cycle_type == CycleType.SEMIMONTHLY:
        if start.day == 10:
            end = date(start.year, start.month, 24)
            next_start = date(start.year, start.month, 25)
        else:  # start.day == 25, guaranteed by normalization/stepping
            next_month = _add_months(date(start.year, start.month, 1), 1)
            end = date(next_month.year, next_month.month, 9)
            next_start = date(next_month.year, next_month.month, 10)
        return end, next_start
    raise ValueError(f"Unsupported cycle type: {cycle_type}")  # pragma: no cover


def get_forecast(
    bills: list[ForecastBill],
    cycle_type: CycleType,
    start_date: date,
    end_date: date,
    starting_balance_cents: int,
    income_per_cycle_cents: int,
) -> ForecastResult:
    if end_date < start_date:
        raise ValueError("end_date must be on or after start_date")

    schedulable: list[ForecastBill] = []
    unscheduled: list[UnscheduledBill] = []
    for bill in bills:
        reason = validate_recurrence_config(bill)
        if reason:
            unscheduled.append(UnscheduledBill(bill_id=bill.id, name=bill.name, reason=reason))
        else:
            schedulable.append(bill)

    current_start = (
        _normalize_semimonthly_start(start_date)
        if cycle_type == CycleType.SEMIMONTHLY
        else start_date
    )

    running_balance = starting_balance_cents
    cycles: list[ForecastCycle] = []

    while current_start <= end_date:
        current_end, next_start = _cycle_bounds(cycle_type, current_start)
        cycle = build_cycle(schedulable, current_start, current_end)
        # Bills are stored (and displayed) as positive amounts throughout Tally
        # (see Bill.amount_cents) - unlike the reference engine, which stores
        # bill amounts pre-negated, so cycle sums subtract here instead of add.
        running_balance += income_per_cycle_cents - cycle.sum_cents
        cycles.append(
            ForecastCycle(
                start_date=current_start,
                end_date=current_end,
                bills=cycle.bills,
                cycle_sum_cents=cycle.sum_cents,
                running_balance_cents=running_balance,
            )
        )
        current_start = next_start

    return ForecastResult(
        cycles=cycles,
        starting_balance_cents=starting_balance_cents,
        ending_balance_cents=running_balance,
        unscheduled_bills=unscheduled,
    )
