from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_bank_account_or_404, get_current_db_user, get_owned_bank_account
from src.bill_events import TRACKED_BILL_FIELDS, created_event, update_events
from src.bills_csv import bills_to_csv, parse_csv_rows
from src.core.database import get_db
from src.forecast import ForecastBill, ForecastCycleOverride, build_bill_history, last_cycle_end
from src.forecast.bill import validate_recurrence_config
from src.models import BankAccount, Bill, BillEvent, CycleOverride, CycleType, RecurrenceType, User
from src.schemas.bill import BillCreate, BillRead, BillUpdate
from src.schemas.bill_event import BillEventListResponse
from src.schemas.bill_history import BillHistoryEntry, BillHistoryResponse

router = APIRouter(prefix="/api/v1/accounts/{account_id}/bills", tags=["bills"])


def _validate_or_422(recurrence_type: RecurrenceType, recurrence_config: dict) -> None:
    reason = validate_recurrence_config(recurrence_type, recurrence_config)
    if reason:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=reason)


async def _get_owned_bill(
    bill_id: int,
    db: AsyncSession = Depends(get_db),
    account: BankAccount = Depends(get_owned_bank_account),
) -> Bill:
    result = await db.execute(
        select(Bill).where(Bill.id == bill_id, Bill.account_id == account.id)
    )
    bill = result.scalar_one_or_none()
    if bill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")
    return bill


@router.get("", response_model=list[BillRead])
async def list_bills(
    db: AsyncSession = Depends(get_db),
    account: BankAccount = Depends(get_owned_bank_account),
) -> list[Bill]:
    result = await db.execute(select(Bill).where(Bill.account_id == account.id))
    return list(result.scalars().all())


@router.post("", response_model=BillRead, status_code=status.HTTP_201_CREATED)
async def create_bill(
    payload: BillCreate,
    db: AsyncSession = Depends(get_db),
    account: BankAccount = Depends(get_owned_bank_account),
) -> Bill:
    _validate_or_422(payload.recurrence_type, payload.recurrence_config)
    bill = Bill(account_id=account.id, **payload.model_dump())
    db.add(bill)
    await db.flush()  # assigns bill.id, needed for the event's FK
    db.add(created_event(bill))
    await db.commit()
    await db.refresh(bill)
    return bill


@router.get("/export")
async def export_bills(
    db: AsyncSession = Depends(get_db),
    account: BankAccount = Depends(get_owned_bank_account),
) -> Response:
    result = await db.execute(select(Bill).where(Bill.account_id == account.id))
    csv_text = bills_to_csv(list(result.scalars().all()))
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="bills-{account.id}.csv"'},
    )


@router.post("/import", response_model=list[BillRead], status_code=status.HTTP_201_CREATED)
async def import_bills(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    account: BankAccount = Depends(get_owned_bank_account),
) -> list[Bill]:
    csv_text = (await file.read()).decode("utf-8-sig")  # -sig strips an Excel-added BOM
    parsed_bills, errors = parse_csv_rows(csv_text)
    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"errors": [{"row": e.row, "message": e.message} for e in errors]},
        )

    bills = [Bill(account_id=account.id, **payload.model_dump()) for payload in parsed_bills]
    db.add_all(bills)
    await db.flush()  # assigns each bill.id, needed for the events' FK
    db.add_all(created_event(bill) for bill in bills)
    ids = [bill.id for bill in bills]
    await db.commit()
    result = await db.execute(select(Bill).where(Bill.id.in_(ids)).order_by(Bill.id))
    return list(result.scalars().all())


@router.patch("/{bill_id}", response_model=BillRead)
async def update_bill(
    payload: BillUpdate,
    db: AsyncSession = Depends(get_db),
    bill: Bill = Depends(_get_owned_bill),
    current_user: User = Depends(get_current_db_user),
) -> Bill:
    update_data = payload.model_dump(exclude_unset=True)
    if "account_id" in update_data:
        # Moving a bill to another account - the target must also belong to
        # the current user, same as the account this route is already
        # scoped to (get_owned_bank_account only validated the *current*
        # account_id from the URL, not the new one in the body).
        await get_bank_account_or_404(update_data["account_id"], db, current_user)
    # Validate the *resulting* combination, not just the patch fields alone -
    # a PATCH that only touches amount_cents must still be checked against
    # whatever recurrence_type/recurrence_config the bill will end up with.
    _validate_or_422(
        update_data.get("recurrence_type", bill.recurrence_type),
        update_data.get("recurrence_config", bill.recurrence_config),
    )
    before = {field: getattr(bill, field) for field in [*TRACKED_BILL_FIELDS, "notes", "enabled"]}
    for field, value in update_data.items():
        setattr(bill, field, value)
    db.add_all(update_events(bill, update_data, before))
    await db.commit()
    await db.refresh(bill)
    return bill


@router.get("/{bill_id}/history", response_model=BillHistoryResponse)
async def get_bill_history(
    db: AsyncSession = Depends(get_db),
    account: BankAccount = Depends(get_owned_bank_account),
    bill: Bill = Depends(_get_owned_bill),
    start_date: date | None = None,
    end_date: date | None = None,
    cycle_type: CycleType | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> BillHistoryResponse:
    # cycle_type isn't a bill-level concept (it's the account's pay-cycle
    # cadence, same as /forecast) - default to whatever the account last used
    # so a plain GET with no params lines up with the cycles the user has
    # actually been reconciling against. Cycle boundaries are computed by
    # stepping forward from start_date (see iter_cycle_bounds), so a
    # cycle_overrides row's cycle_start_date only matches what we regenerate
    # here if we anchor on the same start_date /forecast used
    # (account.forecast_start_date) - anchoring on the bill's own start_date
    # instead would produce a different, non-overlapping series of cycle
    # boundaries whenever the two dates disagree.
    effective_cycle_type = cycle_type or account.forecast_cycle_type or CycleType.MONTHLY
    effective_start = start_date or account.forecast_start_date or bill.start_date
    effective_end = end_date or date.today()
    if effective_end < effective_start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_date must be on or after start_date",
        )

    reason = validate_recurrence_config(bill.recurrence_type, bill.recurrence_config)
    if reason:
        return BillHistoryResponse(bill_id=bill.id, total=0, entries=[])

    forecast_bill = ForecastBill(
        id=bill.id,
        name=bill.name,
        amount_cents=bill.amount_cents,
        recurrence_type=bill.recurrence_type,
        recurrence_config=bill.recurrence_config,
        start_date=bill.start_date,
        end_date=bill.end_date,
    )

    # Bound the same way /forecast does: the last cycle can run past
    # effective_end depending on cycle_type, so query overrides up to its
    # real end rather than effective_end directly.
    query_end_date = last_cycle_end(effective_cycle_type, effective_start, effective_end)
    overrides_result = await db.execute(
        select(CycleOverride).where(
            CycleOverride.account_id == account.id,
            CycleOverride.bill_id == bill.id,
            CycleOverride.cycle_start_date >= effective_start,
            CycleOverride.cycle_start_date <= query_end_date,
        )
    )
    overrides_by_cycle_start = {
        override.cycle_start_date: ForecastCycleOverride(
            bill_id=override.bill_id,
            windfall_id=override.windfall_id,
            cycle_start_date=override.cycle_start_date,
            completed=override.completed,
            override_amount_cents=override.override_amount_cents,
            notes=override.notes,
        )
        for override in overrides_result.scalars().all()
    }

    lines = build_bill_history(
        forecast_bill, effective_cycle_type, effective_start, effective_end, overrides_by_cycle_start
    )
    lines.sort(key=lambda line: line.due_date, reverse=True)

    total = len(lines)
    page = lines[offset : offset + limit]
    return BillHistoryResponse(
        bill_id=bill.id,
        total=total,
        entries=[
            BillHistoryEntry(
                cycle_start_date=line.cycle_start_date,
                cycle_end_date=line.cycle_end_date,
                due_date=line.due_date,
                expected_amount_cents=line.expected_amount_cents,
                actual_amount_cents=line.actual_amount_cents,
                completed=line.completed,
                notes=line.notes,
                variance_cents=line.variance_cents,
            )
            for line in page
        ],
    )


@router.get("/{bill_id}/events", response_model=BillEventListResponse)
async def get_bill_events(
    db: AsyncSession = Depends(get_db),
    bill: Bill = Depends(_get_owned_bill),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> BillEventListResponse:
    count_result = await db.execute(
        select(func.count()).select_from(BillEvent).where(BillEvent.bill_id == bill.id)
    )
    total = count_result.scalar_one()
    result = await db.execute(
        select(BillEvent)
        .where(BillEvent.bill_id == bill.id)
        .order_by(BillEvent.created_at.desc(), BillEvent.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return BillEventListResponse(bill_id=bill.id, total=total, events=list(result.scalars().all()))


@router.delete("/{bill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bill(
    db: AsyncSession = Depends(get_db),
    bill: Bill = Depends(_get_owned_bill),
) -> None:
    await db.delete(bill)
    await db.commit()
