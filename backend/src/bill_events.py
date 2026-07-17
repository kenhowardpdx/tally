from __future__ import annotations

import enum
from datetime import date, datetime
from typing import Any

from src.models import Bill, BillEvent, BillEventType

# Fields that collapse into a single "updated" event when changed together
# in one PATCH - notes and enabled get their own typed events below instead,
# so the timeline can call those out distinctly.
TRACKED_BILL_FIELDS = [
    "name",
    "amount_cents",
    "recurrence_type",
    "recurrence_config",
    "start_date",
    "end_date",
    "account_id",
]


def _json_safe(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, enum.Enum):
        return value.value
    return value


def created_event(bill: Bill) -> BillEvent:
    return BillEvent(
        account_id=bill.account_id,
        bill_id=bill.id,
        event_type=BillEventType.CREATED,
        changes={
            field: _json_safe(getattr(bill, field))
            for field in [*TRACKED_BILL_FIELDS, "enabled", "notes"]
        },
    )


def disabled_event(bill: Bill) -> BillEvent:
    """A plain DISABLED event with no per-field diff - used wherever a bill
    is disabled other than through a user-initiated PATCH (which goes
    through update_events instead): auto-disabled because its end_date has
    passed (_auto_disable_expired in src/api/bills.py), or disabled because
    a CSV reimport omitted it (src/api/bills.py's import/commit). The
    timeline labels every DISABLED event the same way regardless of cause.
    """
    return BillEvent(account_id=bill.account_id, bill_id=bill.id, event_type=BillEventType.DISABLED)


def update_events(
    bill: Bill, update_data: dict[str, Any], before: dict[str, Any]
) -> list[BillEvent]:
    """Diffs `before` (a field snapshot taken prior to mutation) against
    `update_data` (the PATCH payload actually applied) into typed events.

    Call after mutations are applied to `bill` - `bill.account_id` must
    already reflect a move to a new account if this update caused one, so
    the resulting events are queryable under wherever the bill lives now.
    """
    events: list[BillEvent] = []

    if "notes" in update_data and update_data["notes"] != before["notes"]:
        events.append(
            BillEvent(
                account_id=bill.account_id,
                bill_id=bill.id,
                event_type=BillEventType.NOTES_CHANGED,
                changes={"notes": {"old": before["notes"], "new": update_data["notes"]}},
            )
        )

    if "enabled" in update_data and update_data["enabled"] != before["enabled"]:
        events.append(
            BillEvent(
                account_id=bill.account_id,
                bill_id=bill.id,
                event_type=(
                    BillEventType.ENABLED if update_data["enabled"] else BillEventType.DISABLED
                ),
            )
        )

    field_changes = {
        field: {"old": _json_safe(before[field]), "new": _json_safe(update_data[field])}
        for field in TRACKED_BILL_FIELDS
        if field in update_data and before[field] != update_data[field]
    }
    if field_changes:
        events.append(
            BillEvent(
                account_id=bill.account_id,
                bill_id=bill.id,
                event_type=BillEventType.UPDATED,
                changes=field_changes,
            )
        )

    return events
