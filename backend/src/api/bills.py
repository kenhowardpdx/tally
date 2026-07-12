from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_bank_account_or_404, get_current_db_user, get_owned_bank_account
from src.bills_csv import bills_to_csv, parse_csv_rows
from src.core.database import get_db
from src.models import BankAccount, Bill, User
from src.schemas.bill import BillCreate, BillRead, BillUpdate

router = APIRouter(prefix="/api/v1/accounts/{account_id}/bills", tags=["bills"])


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
    bill = Bill(account_id=account.id, **payload.model_dump())
    db.add(bill)
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
    await db.commit()
    for bill in bills:
        await db.refresh(bill)
    return bills


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
    for field, value in update_data.items():
        setattr(bill, field, value)
    await db.commit()
    await db.refresh(bill)
    return bill


@router.delete("/{bill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bill(
    db: AsyncSession = Depends(get_db),
    bill: Bill = Depends(_get_owned_bill),
) -> None:
    await db.delete(bill)
    await db.commit()
