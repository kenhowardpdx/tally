from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_owned_bank_account
from src.core.database import get_db
from src.models import BankAccount, Bill
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


@router.patch("/{bill_id}", response_model=BillRead)
async def update_bill(
    payload: BillUpdate,
    db: AsyncSession = Depends(get_db),
    bill: Bill = Depends(_get_owned_bill),
) -> Bill:
    for field, value in payload.model_dump(exclude_unset=True).items():
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
