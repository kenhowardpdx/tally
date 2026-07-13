from __future__ import annotations

from calendar import monthrange
from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date, timedelta

from src.forecast.bill import ForecastBill, validate_recurrence_config
from src.forecast.cycle import (
    CycleBillLine,
    CycleTransactionLine,
    CycleWindfallLine,
    build_cycle,
)
from src.forecast.cycle_override import ForecastCycleOverride
from src.forecast.transaction import ForecastTransaction
from src.forecast.windfall import ForecastWindfall
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
    transactions: list[CycleTransactionLine]
    windfalls: list[CycleWindfallLine]
    net_cents: int
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


def _cycle_bounds(cycle_type: CycleType, start: date) -> tuple[date, date]:
    """Given a cycle's start date, returns (this cycle's end date, next
    cycle's start date).

    For SEMIMONTHLY this deliberately does NOT snap `start` backward onto the
    nearest 10th/25th boundary first - only the END of whatever half-month
    period `start` currently falls in, and the START of the next one. Doing
    otherwise would silently include bills from before the caller's actual
    start_date in the first cycle, corrupting the meaning of
    starting_balance_cents (it's meant to be the balance as of start_date,
    not as of some earlier snapped date). The first cycle can end up shorter
    than a full half-month as a result (e.g. start_date the 21st produces a
    21st-24th first cycle) - every cycle after that is a full period, since
    `next_start` here is always exactly the 10th or 25th.
    """
    if cycle_type == CycleType.WEEKLY:
        return start + timedelta(days=6), start + timedelta(days=7)
    if cycle_type == CycleType.BIWEEKLY:
        return start + timedelta(days=13), start + timedelta(days=14)
    if cycle_type == CycleType.MONTHLY:
        next_start = _add_months(start, 1)
        return next_start - timedelta(days=1), next_start
    if cycle_type == CycleType.SEMIMONTHLY:
        if start.day <= 9:
            end = date(start.year, start.month, 9)
            next_start = date(start.year, start.month, 10)
        elif start.day <= 24:
            end = date(start.year, start.month, 24)
            next_start = date(start.year, start.month, 25)
        else:  # start.day >= 25
            next_month = _add_months(date(start.year, start.month, 1), 1)
            end = date(next_month.year, next_month.month, 9)
            next_start = date(next_month.year, next_month.month, 10)
        return end, next_start
    raise ValueError(f"Unsupported cycle type: {cycle_type}")  # pragma: no cover


def iter_cycle_bounds(
    cycle_type: CycleType, start_date: date, end_date: date
) -> Iterator[tuple[date, date]]:
    """Yields (cycle_start, cycle_end) for each cycle get_forecast() would
    generate between start_date and end_date. Shared by get_forecast(),
    last_cycle_end(), and build_bill_history() so all three agree on exactly
    where cycles fall. Public (no leading underscore) for that last caller,
    which lives outside this module.
    """
    if end_date < start_date:
        raise ValueError("end_date must be on or after start_date")

    current_start = start_date
    while current_start <= end_date:
        current_end, next_start = _cycle_bounds(cycle_type, current_start)
        yield current_start, current_end
        current_start = next_start


def last_cycle_end(cycle_type: CycleType, start_date: date, end_date: date) -> date:
    """The end date of the last cycle get_forecast() would generate for the
    same (cycle_type, start_date, end_date).

    Cycles don't snap to end_date, so the final one can run past it (see
    _cycle_bounds) - callers that need to bound a query to "every date any
    cycle could touch" (e.g. an upper bound for loading transactions/
    windfalls) should use this instead of end_date directly.
    """
    last_end: date | None = None
    for _, current_end in iter_cycle_bounds(cycle_type, start_date, end_date):
        last_end = current_end
    assert last_end is not None  # iter_cycle_bounds always yields at least one cycle
    return last_end


def _shift_cycle_start(cycle_type: CycleType, start: date, periods: int) -> date:
    """Moves `start` forward (positive `periods`) or backward (negative) by
    whole cycle periods. Only meaningful for the self-anchoring-free types
    (weekly/biweekly/monthly) - semimonthly's boundaries don't shift by a
    fixed period (see _cycle_bounds's SEMIMONTHLY branch), so callers handle
    it separately.
    """
    if cycle_type == CycleType.WEEKLY:
        return start + timedelta(days=7 * periods)
    if cycle_type == CycleType.BIWEEKLY:
        return start + timedelta(days=14 * periods)
    if cycle_type == CycleType.MONTHLY:
        return _add_months(start, periods)
    raise ValueError(f"Unsupported cycle type: {cycle_type}")  # pragma: no cover


def find_current_cycle_bounds(
    cycle_type: CycleType, anchor_start_date: date, today: date
) -> tuple[date, date]:
    """Finds the (start, end) of whichever cycle contains `today`, for a
    sequence of cycles anchored at `anchor_start_date` (an account's saved
    `forecast_start_date`).

    Weekly/biweekly/monthly cycles only snap to whatever start date a caller
    gives them (unlike semimonthly's fixed 10th/25th boundaries), so "the
    cycle containing today" has to be derived by walking from the anchor
    rather than computed from today alone. Semimonthly ignores the anchor
    entirely and walks from the 1st of today's month instead, since its
    boundaries are fixed regardless of where any particular forecast run
    started.
    """
    if cycle_type == CycleType.SEMIMONTHLY:
        # Exact, not an estimate: a steady-state semimonthly cycle only ever
        # starts on the 10th or 25th (see _cycle_bounds - next_start is
        # always one of those two), so today's day alone determines which
        # bucket - and its start - today falls in.
        if today.day <= 9:
            prev_month = _add_months(date(today.year, today.month, 1), -1)
            candidate = date(prev_month.year, prev_month.month, 25)
        elif today.day <= 24:
            candidate = date(today.year, today.month, 10)
        else:
            candidate = date(today.year, today.month, 25)
    else:
        # Closed-form estimate of how many whole periods separate the anchor
        # from today, to avoid iterating one cycle at a time when the anchor
        # is far in the past/future. Exact for weekly/biweekly; monthly's
        # variable month lengths make this an estimate, not exact - the
        # correction loop below fixes any off-by-one.
        if cycle_type == CycleType.WEEKLY:
            periods = (today - anchor_start_date).days // 7
        elif cycle_type == CycleType.BIWEEKLY:
            periods = (today - anchor_start_date).days // 14
        elif cycle_type == CycleType.MONTHLY:
            periods = (today.year - anchor_start_date.year) * 12 + (
                today.month - anchor_start_date.month
            )
            if today.day < anchor_start_date.day:
                periods -= 1
        else:  # pragma: no cover - exhaustive over CycleType
            raise ValueError(f"Unsupported cycle type: {cycle_type}")
        candidate = _shift_cycle_start(cycle_type, anchor_start_date, periods)

    # Semimonthly's candidate (the 1st of today's month) is always <= today
    # by construction, so this only ever runs for the anchored types.
    while candidate > today:
        candidate = _shift_cycle_start(cycle_type, candidate, -1)
    while True:
        end, next_start = _cycle_bounds(cycle_type, candidate)
        if today <= end:
            return candidate, end
        candidate = next_start


def get_forecast(
    bills: list[ForecastBill],
    cycle_type: CycleType,
    start_date: date,
    end_date: date,
    starting_balance_cents: int,
    income_per_cycle_cents: int,
    transactions: list[ForecastTransaction] | None = None,
    windfalls: list[ForecastWindfall] | None = None,
    overrides: list[ForecastCycleOverride] | None = None,
) -> ForecastResult:
    transactions = transactions or []
    windfalls = windfalls or []

    # Group by cycle_start_date first, then by target id, since a
    # cycle_overrides row only applies to the one cycle it names - build_cycle
    # needs just the slice relevant to the cycle it's currently building.
    bill_overrides_by_cycle_start: dict[date, dict[int, ForecastCycleOverride]] = defaultdict(dict)
    windfall_overrides_by_cycle_start: dict[date, dict[int, ForecastCycleOverride]] = defaultdict(
        dict
    )
    for override in overrides or []:
        if override.bill_id is not None:
            bill_overrides_by_cycle_start[override.cycle_start_date][override.bill_id] = override
        else:
            windfall_overrides_by_cycle_start[override.cycle_start_date][
                override.windfall_id
            ] = override

    schedulable: list[ForecastBill] = []
    unscheduled: list[UnscheduledBill] = []
    for bill in bills:
        reason = validate_recurrence_config(bill.recurrence_type, bill.recurrence_config)
        if reason:
            unscheduled.append(UnscheduledBill(bill_id=bill.id, name=bill.name, reason=reason))
        else:
            schedulable.append(bill)

    running_balance = starting_balance_cents
    cycles: list[ForecastCycle] = []

    for current_start, current_end in iter_cycle_bounds(cycle_type, start_date, end_date):
        cycle = build_cycle(
            schedulable,
            transactions,
            windfalls,
            current_start,
            current_end,
            bill_overrides=bill_overrides_by_cycle_start.get(current_start),
            windfall_overrides=windfall_overrides_by_cycle_start.get(current_start),
        )
        running_balance += income_per_cycle_cents + cycle.net_cents
        cycles.append(
            ForecastCycle(
                start_date=current_start,
                end_date=current_end,
                bills=cycle.bills,
                transactions=cycle.transactions,
                windfalls=cycle.windfalls,
                net_cents=cycle.net_cents,
                running_balance_cents=running_balance,
            )
        )

    return ForecastResult(
        cycles=cycles,
        starting_balance_cents=starting_balance_cents,
        ending_balance_cents=running_balance,
        unscheduled_bills=unscheduled,
    )
