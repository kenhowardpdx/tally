from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from src.forecast.bill import ForecastBill, occurrences_in_range
from src.forecast.cycle_override import ForecastCycleOverride
from src.forecast.transaction import ForecastTransaction
from src.forecast.windfall import ForecastWindfall


@dataclass
class CycleBillLine:
    bill_id: int
    name: str
    # The amount actually used in the running balance for this occurrence -
    # the override's amount if one is set on the first occurrence, else
    # forecasted_amount_cents.
    amount_cents: int
    # The bill's own configured amount, regardless of any override - lets
    # callers show forecasted-vs-actual and compute variance.
    forecasted_amount_cents: int
    due_date: date
    completed: bool
    notes: str | None


@dataclass
class CycleTransactionLine:
    transaction_id: int
    amount_cents: int
    date: date
    description: str | None


@dataclass
class CycleWindfallLine:
    windfall_id: int
    name: str
    amount_cents: int
    forecasted_amount_cents: int
    expected_date: date
    completed: bool
    notes: str | None


@dataclass
class Cycle:
    bills: list[CycleBillLine]
    transactions: list[CycleTransactionLine]
    windfalls: list[CycleWindfallLine]
    # Net balance impact for this cycle: transactions (signed) + windfalls
    # (always positive) - bills (always positive, always an expense).
    net_cents: int


def build_cycle(
    bills: list[ForecastBill],
    transactions: list[ForecastTransaction],
    windfalls: list[ForecastWindfall],
    start: date,
    end: date,
    bill_overrides: dict[int, ForecastCycleOverride] | None = None,
    windfall_overrides: dict[int, ForecastCycleOverride] | None = None,
) -> Cycle:
    """Bills/transactions/windfalls falling within [start, end], each sorted
    by date, plus the combined net balance impact.

    `bills` must already be pre-filtered to ones with valid recurrence_config
    (see validate_recurrence_config) - this raises MissingRecurrenceConfig
    otherwise, same as occurrences_in_range. Transactions and windfalls are
    one-off (a single date each), so unlike bills there's no recurrence/
    due-date computation - just a plain date-range check.

    `bill_overrides`/`windfall_overrides` are keyed by bill_id/windfall_id and
    must already be pre-filtered by the caller to overrides whose
    cycle_start_date equals `start` (a cycle_overrides row is scoped to one
    specific cycle, identified by its start date). A bill can recur more than
    once within a single cycle (e.g. weekly inside a monthly forecast) but
    cycle_overrides has only one row per (bill, cycle_start_date), so the
    override applies to just the first occurrence in the cycle; later
    occurrences use the bill's base amount.
    """
    bill_overrides = bill_overrides or {}
    windfall_overrides = windfall_overrides or {}

    bill_lines: list[CycleBillLine] = []
    for bill in bills:
        override = bill_overrides.get(bill.id)
        for index, occurrence in enumerate(occurrences_in_range(bill, start, end)):
            apply_override = override is not None and index == 0
            amount_cents = (
                override.override_amount_cents
                if apply_override and override.override_amount_cents is not None
                else bill.amount_cents
            )
            bill_lines.append(
                CycleBillLine(
                    bill_id=bill.id,
                    name=bill.name,
                    amount_cents=amount_cents,
                    forecasted_amount_cents=bill.amount_cents,
                    due_date=occurrence,
                    completed=override.completed if apply_override else False,
                    notes=override.notes if apply_override else None,
                )
            )
    bill_lines.sort(key=lambda line: (line.due_date, line.bill_id))
    bills_total = sum(line.amount_cents for line in bill_lines)

    transaction_lines = [
        CycleTransactionLine(
            transaction_id=t.id,
            amount_cents=t.amount_cents,
            date=t.date,
            description=t.description,
        )
        for t in transactions
        if start <= t.date <= end
    ]
    transaction_lines.sort(key=lambda line: (line.date, line.transaction_id))
    transactions_total = sum(line.amount_cents for line in transaction_lines)

    windfall_lines = []
    for w in windfalls:
        if not (start <= w.expected_date <= end):
            continue
        override = windfall_overrides.get(w.id)
        amount_cents = (
            override.override_amount_cents
            if override is not None and override.override_amount_cents is not None
            else w.amount_cents
        )
        windfall_lines.append(
            CycleWindfallLine(
                windfall_id=w.id,
                name=w.name,
                amount_cents=amount_cents,
                forecasted_amount_cents=w.amount_cents,
                expected_date=w.expected_date,
                completed=override.completed if override is not None else False,
                notes=override.notes if override is not None else None,
            )
        )
    windfall_lines.sort(key=lambda line: (line.expected_date, line.windfall_id))
    windfalls_total = sum(line.amount_cents for line in windfall_lines)

    net_cents = transactions_total + windfalls_total - bills_total

    return Cycle(
        bills=bill_lines,
        transactions=transaction_lines,
        windfalls=windfall_lines,
        net_cents=net_cents,
    )
