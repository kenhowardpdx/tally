from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta

from src.models.bill import RecurrenceType


class MissingRecurrenceConfig(Exception):
    """A bill's recurrence_type needs recurrence_config data that isn't set.

    Raised for `semimonthly`/`custom_days` bills created before the UI to collect
    that config exists (roadmap 1.7) - the forecast engine treats this as a
    per-bill "can't be scheduled" condition, not a hard failure.
    """


@dataclass
class ForecastBill:
    """A bill, decoupled from the SQLAlchemy model so the engine has no ORM/DB
    dependency and stays easy to unit test in isolation."""

    id: int
    name: str
    amount_cents: int
    recurrence_type: RecurrenceType
    recurrence_config: dict
    start_date: date
    end_date: date | None


def _last_day_of_month(year: int, month: int) -> int:
    return monthrange(year, month)[1]


def _clamp_day(year: int, month: int, day: int) -> int:
    # A bill anchored on the 31st is due on the 28th/29th/30th in shorter
    # months, rather than overflowing into the next month.
    return min(day, _last_day_of_month(year, month))


def validate_recurrence_config(bill: ForecastBill) -> str | None:
    """Returns a human-readable reason if `bill.recurrence_config` is missing data
    required for its recurrence_type, else None."""
    if bill.recurrence_type == RecurrenceType.SEMIMONTHLY:
        days = bill.recurrence_config.get("days")
        if not isinstance(days, list) or not days or not all(isinstance(d, int) for d in days):
            return "semimonthly bills need recurrence_config.days, e.g. [10, 25]"
    if bill.recurrence_type == RecurrenceType.CUSTOM_DAYS:
        interval = bill.recurrence_config.get("interval_days")
        if not isinstance(interval, int) or interval <= 0:
            return "custom_days bills need recurrence_config.interval_days"
    return None


def _within_bill_lifetime(bill: ForecastBill, occurrence: date) -> bool:
    if occurrence < bill.start_date:
        return False
    if bill.end_date and occurrence > bill.end_date:
        return False
    return True


def _monthly_occurrences(bill: ForecastBill, cycle_start: date, cycle_end: date) -> list[date]:
    day = bill.start_date.day
    occurrences = set()
    for year, month in {(cycle_start.year, cycle_start.month), (cycle_end.year, cycle_end.month)}:
        candidate = date(year, month, _clamp_day(year, month, day))
        if cycle_start <= candidate <= cycle_end:
            occurrences.add(candidate)
    return sorted(occurrences)


def _annually_occurrences(bill: ForecastBill, cycle_start: date, cycle_end: date) -> list[date]:
    month, day = bill.start_date.month, bill.start_date.day
    occurrences = set()
    for year in {cycle_start.year, cycle_end.year}:
        candidate = date(year, month, _clamp_day(year, month, day))
        if cycle_start <= candidate <= cycle_end:
            occurrences.add(candidate)
    return sorted(occurrences)


def _semimonthly_occurrences(bill: ForecastBill, cycle_start: date, cycle_end: date) -> list[date]:
    days = bill.recurrence_config["days"]
    occurrences = set()
    for year, month in {(cycle_start.year, cycle_start.month), (cycle_end.year, cycle_end.month)}:
        for day in days:
            candidate = date(year, month, _clamp_day(year, month, day))
            if cycle_start <= candidate <= cycle_end:
                occurrences.add(candidate)
    return sorted(occurrences)


def _interval_occurrences(
    anchor: date, interval_days: int, cycle_start: date, cycle_end: date
) -> list[date]:
    """All `anchor + k*interval_days` occurrences (k >= 0) landing in
    [cycle_start, cycle_end]. Generalizes the reference's single-occurrence-per-
    cycle model: a weekly bill inside a monthly cycle can genuinely recur more
    than once in that window, and each occurrence should count."""
    if cycle_end < anchor:
        return []
    effective_start = max(cycle_start, anchor)
    offset_days = (effective_start - anchor).days
    first_k = -(-offset_days // interval_days)  # ceil division

    occurrences = []
    k = first_k
    while True:
        candidate = anchor + timedelta(days=k * interval_days)
        if candidate > cycle_end:
            break
        occurrences.append(candidate)
        k += 1
    return occurrences


def occurrences_in_range(bill: ForecastBill, cycle_start: date, cycle_end: date) -> list[date]:
    """All due-date occurrences of `bill` that fall within [cycle_start, cycle_end].

    Raises MissingRecurrenceConfig if the bill's recurrence_type needs config data
    that's absent - callers iterating many bills should pre-filter with
    validate_recurrence_config instead of catching this per-call.
    """
    reason = validate_recurrence_config(bill)
    if reason:
        raise MissingRecurrenceConfig(reason)

    if bill.recurrence_type == RecurrenceType.MONTHLY:
        raw = _monthly_occurrences(bill, cycle_start, cycle_end)
    elif bill.recurrence_type == RecurrenceType.ANNUALLY:
        raw = _annually_occurrences(bill, cycle_start, cycle_end)
    elif bill.recurrence_type == RecurrenceType.SEMIMONTHLY:
        raw = _semimonthly_occurrences(bill, cycle_start, cycle_end)
    elif bill.recurrence_type == RecurrenceType.WEEKLY:
        raw = _interval_occurrences(bill.start_date, 7, cycle_start, cycle_end)
    elif bill.recurrence_type == RecurrenceType.BIWEEKLY:
        raw = _interval_occurrences(bill.start_date, 14, cycle_start, cycle_end)
    elif bill.recurrence_type == RecurrenceType.CUSTOM_DAYS:
        interval_days = bill.recurrence_config["interval_days"]
        raw = _interval_occurrences(bill.start_date, interval_days, cycle_start, cycle_end)
    else:  # pragma: no cover - exhaustive over RecurrenceType
        raise ValueError(f"Unsupported recurrence type: {bill.recurrence_type}")

    return [occurrence for occurrence in raw if _within_bill_lifetime(bill, occurrence)]
