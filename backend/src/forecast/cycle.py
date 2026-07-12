from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from src.forecast.bill import ForecastBill, occurrences_in_range


@dataclass
class CycleBillLine:
    bill_id: int
    name: str
    amount_cents: int
    due_date: date


@dataclass
class Cycle:
    bills: list[CycleBillLine]
    sum_cents: int


def build_cycle(bills: list[ForecastBill], start: date, end: date) -> Cycle:
    """Bills due within [start, end], sorted by due date, with the total.

    `bills` must already be pre-filtered to ones with valid recurrence_config
    (see validate_recurrence_config) - this raises MissingRecurrenceConfig
    otherwise, same as occurrences_in_range.
    """
    lines: list[CycleBillLine] = []
    for bill in bills:
        for occurrence in occurrences_in_range(bill, start, end):
            lines.append(
                CycleBillLine(
                    bill_id=bill.id,
                    name=bill.name,
                    amount_cents=bill.amount_cents,
                    due_date=occurrence,
                )
            )
    lines.sort(key=lambda line: (line.due_date, line.bill_id))
    total = sum(line.amount_cents for line in lines)
    return Cycle(bills=lines, sum_cents=total)
