from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class ForecastWindfall:
    """A one-time future income event (bonus, tax refund, etc.), decoupled
    from the SQLAlchemy model. amount_cents is always positive - a windfall
    is income by definition, unlike the signed ForecastTransaction."""

    id: int
    name: str
    amount_cents: int
    expected_date: date
