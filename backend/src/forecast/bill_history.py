from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from src.forecast.bill import ForecastBill, occurrences_in_range
from src.forecast.cycle_override import ForecastCycleOverride
from src.forecast.engine import iter_cycle_bounds
from src.models.bank_account import CycleType


@dataclass
class BillHistoryLine:
    cycle_start_date: date
    cycle_end_date: date
    due_date: date
    expected_amount_cents: int
    actual_amount_cents: int
    completed: bool
    notes: str | None
    variance_cents: int


def build_bill_history(
    bill: ForecastBill,
    cycle_type: CycleType,
    start_date: date,
    end_date: date,
    overrides_by_cycle_start: dict[date, ForecastCycleOverride],
) -> list[BillHistoryLine]:
    """One entry per due-date occurrence of `bill` within [start_date, end_date],
    grouped by the pay cycle (per `cycle_type`) it falls in - the same cycle
    boundaries get_forecast() would compute, so a cycle_overrides row (keyed
    by cycle_start_date) lines up with the right occurrence here.

    `bill` must already have valid recurrence_config (see
    validate_recurrence_config) - callers should skip bills that don't rather
    than call this, same precondition as build_cycle().

    If a bill recurs more than once within a single pay cycle, only the
    first occurrence in that cycle picks up the override, mirroring
    build_cycle()'s same one-row-per-cycle limitation.
    """
    entries: list[BillHistoryLine] = []
    for cycle_start, cycle_end in iter_cycle_bounds(cycle_type, start_date, end_date):
        override = overrides_by_cycle_start.get(cycle_start)
        for index, due_date in enumerate(occurrences_in_range(bill, cycle_start, cycle_end)):
            apply_override = override is not None and index == 0
            actual_amount_cents = (
                override.override_amount_cents
                if apply_override and override.override_amount_cents is not None
                else bill.amount_cents
            )
            entries.append(
                BillHistoryLine(
                    cycle_start_date=cycle_start,
                    cycle_end_date=cycle_end,
                    due_date=due_date,
                    expected_amount_cents=bill.amount_cents,
                    actual_amount_cents=actual_amount_cents,
                    completed=override.completed if apply_override else False,
                    notes=override.notes if apply_override else None,
                    variance_cents=actual_amount_cents - bill.amount_cents,
                )
            )
    return entries
