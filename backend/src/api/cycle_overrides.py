from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_bank_account_or_404, get_current_db_user, get_owned_bank_account
from src.core.database import get_db
from src.models import BankAccount, Bill, BillEvent, BillEventType, CycleOverride, User, Windfall
from src.schemas.cycle_override import CycleOverrideRead, CycleOverrideUpsert

router = APIRouter(tags=["cycle-overrides"])


async def _validate_target_belongs_to_account(
    db: AsyncSession, account_id: int, bill_id: int | None, windfall_id: int | None
) -> None:
    if bill_id is not None:
        result = await db.execute(
            select(Bill.id).where(Bill.id == bill_id, Bill.account_id == account_id)
        )
        not_found_detail = "Bill not found"
    else:
        result = await db.execute(
            select(Windfall.id).where(
                Windfall.id == windfall_id, Windfall.account_id == account_id
            )
        )
        not_found_detail = "Windfall not found"
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found_detail)


@router.put("/api/v1/cycle-overrides", response_model=CycleOverrideRead)
async def upsert_cycle_override(
    payload: CycleOverrideUpsert,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_db_user),
) -> CycleOverride:
    account = await get_bank_account_or_404(payload.account_id, db, current_user)
    await _validate_target_belongs_to_account(
        db, account.id, payload.bill_id, payload.windfall_id
    )

    key_column = CycleOverride.bill_id if payload.bill_id is not None else CycleOverride.windfall_id
    key_value = payload.bill_id if payload.bill_id is not None else payload.windfall_id
    result = await db.execute(
        select(CycleOverride).where(
            CycleOverride.account_id == account.id,
            key_column == key_value,
            CycleOverride.cycle_start_date == payload.cycle_start_date,
        )
    )
    override = result.scalar_one_or_none()
    is_new = override is None
    # A brand-new override always starts from these defaults (matching
    # CycleOverride's column defaults) - reading them off `override` itself
    # here would race the ORM's flush-time default application.
    before_completed = False if is_new else override.completed
    before_amount_cents = None if is_new else override.override_amount_cents
    before_notes = None if is_new else override.notes

    if is_new:
        override = CycleOverride(
            account_id=account.id,
            bill_id=payload.bill_id,
            windfall_id=payload.windfall_id,
            cycle_start_date=payload.cycle_start_date,
        )
        db.add(override)

    override.completed = payload.completed
    override.override_amount_cents = payload.override_amount_cents
    override.notes = payload.notes

    # Cycle-scoped audit trail is bill-specific (the ask was a bill history
    # feature) - windfalls don't get BillEvent rows.
    if payload.bill_id is not None:
        if payload.completed != before_completed:
            db.add(
                BillEvent(
                    account_id=account.id,
                    bill_id=payload.bill_id,
                    event_type=(
                        BillEventType.CYCLE_MARKED_PAID
                        if payload.completed
                        else BillEventType.CYCLE_MARKED_UNPAID
                    ),
                    cycle_start_date=payload.cycle_start_date,
                )
            )
        if payload.override_amount_cents != before_amount_cents:
            db.add(
                BillEvent(
                    account_id=account.id,
                    bill_id=payload.bill_id,
                    event_type=BillEventType.CYCLE_AMOUNT_CHANGED,
                    cycle_start_date=payload.cycle_start_date,
                    changes={
                        "override_amount_cents": {
                            "old": before_amount_cents,
                            "new": payload.override_amount_cents,
                        }
                    },
                )
            )
        if payload.notes != before_notes:
            db.add(
                BillEvent(
                    account_id=account.id,
                    bill_id=payload.bill_id,
                    event_type=BillEventType.CYCLE_NOTES_CHANGED,
                    cycle_start_date=payload.cycle_start_date,
                    changes={"notes": {"old": before_notes, "new": payload.notes}},
                )
            )

    await db.commit()
    await db.refresh(override)
    return override


@router.get(
    "/api/v1/accounts/{account_id}/cycle-overrides", response_model=list[CycleOverrideRead]
)
async def list_cycle_overrides(
    cycle_start: date,
    db: AsyncSession = Depends(get_db),
    account: BankAccount = Depends(get_owned_bank_account),
) -> list[CycleOverride]:
    result = await db.execute(
        select(CycleOverride).where(
            CycleOverride.account_id == account.id,
            CycleOverride.cycle_start_date == cycle_start,
        )
    )
    return list(result.scalars().all())
