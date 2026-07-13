import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class BillEventType(str, enum.Enum):
    CREATED = "created"
    UPDATED = "updated"
    NOTES_CHANGED = "notes_changed"
    ENABLED = "enabled"
    DISABLED = "disabled"
    CYCLE_MARKED_PAID = "cycle_marked_paid"
    CYCLE_MARKED_UNPAID = "cycle_marked_unpaid"
    CYCLE_AMOUNT_CHANGED = "cycle_amount_changed"
    CYCLE_NOTES_CHANGED = "cycle_notes_changed"


class BillEvent(Base):
    """Append-only audit trail for a bill - distinct from `cycle_overrides`
    (current reconciliation state) and `bill_history` (forecasted-vs-actual
    per cycle, derived from that state). Never updated after insert."""

    __tablename__ = "bill_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("bank_accounts.id", ondelete="CASCADE"), index=True
    )
    bill_id: Mapped[int] = mapped_column(ForeignKey("bills.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[BillEventType] = mapped_column(
        Enum(
            BillEventType,
            name="bill_event_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        )
    )
    # Set only for cycle-scoped events (cycle_marked_paid/unpaid,
    # cycle_amount_changed, cycle_notes_changed); NULL for bill-level
    # lifecycle events (created/updated/notes_changed/enabled/disabled).
    cycle_start_date: Mapped[date | None] = mapped_column(Date)
    # Per-field {"old": ..., "new": ...} pairs; which keys appear depends on
    # event_type (e.g. {"notes": {...}} for notes_changed, one entry per
    # changed field for "updated").
    changes: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    bill: Mapped["Bill"] = relationship(back_populates="events")
