from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_db_user, get_owned_bank_account
from src.core.database import get_db
from src.models import BankAccount, User
from src.schemas.bank_account import BankAccountCreate, BankAccountRead, BankAccountUpdate

router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])


@router.get("", response_model=list[BankAccountRead])
async def list_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_db_user),
) -> list[BankAccount]:
    result = await db.execute(
        select(BankAccount).where(BankAccount.user_id == current_user.id)
    )
    return list(result.scalars().all())


@router.post("", response_model=BankAccountRead, status_code=status.HTTP_201_CREATED)
async def create_account(
    payload: BankAccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_db_user),
) -> BankAccount:
    account = BankAccount(user_id=current_user.id, **payload.model_dump())
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


@router.get("/{account_id}", response_model=BankAccountRead)
async def get_account(account: BankAccount = Depends(get_owned_bank_account)) -> BankAccount:
    return account


@router.patch("/{account_id}", response_model=BankAccountRead)
async def update_account(
    payload: BankAccountUpdate,
    db: AsyncSession = Depends(get_db),
    account: BankAccount = Depends(get_owned_bank_account),
) -> BankAccount:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(account, field, value)
    await db.commit()
    await db.refresh(account)
    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    db: AsyncSession = Depends(get_db),
    account: BankAccount = Depends(get_owned_bank_account),
) -> None:
    await db.delete(account)
    await db.commit()
