from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from src.forecast.bill import ForecastBill, occurrences_in_range
from src.forecast.transaction import ForecastTransaction
from src.forecast.windfall import ForecastWindfall


@dataclass
class CycleBillLine:
    bill_id: int
    name: str
    amount_cents: int
    due_date: date


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
    expected_date: date


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
) -> Cycle:
    """Bills/transactions/windfalls falling within [start, end], each sorted
    by date, plus the combined net balance impact.

    `bills` must already be pre-filtered to ones with valid recurrence_config
    (see validate_recurrence_config) - this raises MissingRecurrenceConfig
    otherwise, same as occurrences_in_range. Transactions and windfalls are
    one-off (a single date each), so unlike bills there's no recurrence/
    due-date computation - just a plain date-range check.
    """
    bill_lines: list[CycleBillLine] = []
    for bill in bills:
        for occurrence in occurrences_in_range(bill, start, end):
            bill_lines.append(
                CycleBillLine(
                    bill_id=bill.id,
                    name=bill.name,
                    amount_cents=bill.amount_cents,
                    due_date=occurrence,
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

    windfall_lines = [
        CycleWindfallLine(
            windfall_id=w.id,
            name=w.name,
            amount_cents=w.amount_cents,
            expected_date=w.expected_date,
        )
        for w in windfalls
        if start <= w.expected_date <= end
    ]
    windfall_lines.sort(key=lambda line: (line.expected_date, line.windfall_id))
    windfalls_total = sum(line.amount_cents for line in windfall_lines)

    net_cents = transactions_total + windfalls_total - bills_total

    return Cycle(
        bills=bill_lines,
        transactions=transaction_lines,
        windfalls=windfall_lines,
        net_cents=net_cents,
    )
