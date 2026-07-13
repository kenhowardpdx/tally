from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class ForecastCycleOverride:
    """A cycle_overrides row, decoupled from the SQLAlchemy model for the same
    reason as ForecastBill/ForecastWindfall - keeps the engine ORM-free.

    Exactly one of bill_id/windfall_id is set, matching the DB's CHECK
    constraint (see CycleOverride).
    """

    bill_id: int | None
    windfall_id: int | None
    cycle_start_date: date
    completed: bool
    override_amount_cents: int | None
    notes: str | None
