from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class ForecastTransaction:
    """A one-off ledger entry, decoupled from the SQLAlchemy model (matches
    ForecastBill's pattern). Unlike a Bill (always a positive expense) or a
    Windfall (always positive income), amount_cents is signed: positive
    credits the balance, negative debits it - a Transaction is the
    general-purpose one-off entry, not restricted to either direction."""

    id: int
    amount_cents: int
    date: date
    description: str | None
