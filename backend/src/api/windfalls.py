from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_owned_bank_account
from src.core.database import get_db
from src.models import BankAccount, Windfall
from src.schemas.windfall import WindfallCreate, WindfallRead, WindfallUpdate

router = APIRouter(prefix="/api/v1/accounts/{account_id}/windfalls", tags=["windfalls"])


async def _get_owned_windfall(
    windfall_id: int,
    db: AsyncSession = Depends(get_db),
    account: BankAccount = Depends(get_owned_bank_account),
) -> Windfall:
    result = await db.execute(
        select(Windfall).where(Windfall.id == windfall_id, Windfall.account_id == account.id)
    )
    windfall = result.scalar_one_or_none()
    if windfall is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Windfall not found")
    return windfall


@router.get("", response_model=list[WindfallRead])
async def list_windfalls(
    db: AsyncSession = Depends(get_db),
    account: BankAccount = Depends(get_owned_bank_account),
) -> list[Windfall]:
    result = await db.execute(select(Windfall).where(Windfall.account_id == account.id))
    return list(result.scalars().all())


@router.post("", response_model=WindfallRead, status_code=status.HTTP_201_CREATED)
async def create_windfall(
    payload: WindfallCreate,
    db: AsyncSession = Depends(get_db),
    account: BankAccount = Depends(get_owned_bank_account),
) -> Windfall:
    windfall = Windfall(account_id=account.id, **payload.model_dump())
    db.add(windfall)
    await db.commit()
    await db.refresh(windfall)
    return windfall


@router.patch("/{windfall_id}", response_model=WindfallRead)
async def update_windfall(
    payload: WindfallUpdate,
    db: AsyncSession = Depends(get_db),
    windfall: Windfall = Depends(_get_owned_windfall),
) -> Windfall:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(windfall, field, value)
    await db.commit()
    await db.refresh(windfall)
    return windfall


@router.delete("/{windfall_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_windfall(
    db: AsyncSession = Depends(get_db),
    windfall: Windfall = Depends(_get_owned_windfall),
) -> None:
    await db.delete(windfall)
    await db.commit()
