from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import get_current_user
from src.core.database import get_db
from src.models import BankAccount, User


async def get_current_db_user(
    claims: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Look up (or JIT-provision) the User row for the authenticated Auth0 subject.

    Only `sub` is guaranteed present on the access token - see the nullability
    note on User.email.
    """
    auth0_sub = claims["sub"]
    result = await db.execute(select(User).where(User.auth0_sub == auth0_sub))
    user = result.scalar_one_or_none()
    if user is not None:
        return user

    user = User(auth0_sub=auth0_sub, email=claims.get("email"))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_bank_account_or_404(
    account_id: int, db: AsyncSession, current_user: User
) -> BankAccount:
    result = await db.execute(
        select(BankAccount).where(
            BankAccount.id == account_id, BankAccount.user_id == current_user.id
        )
    )
    account = result.scalar_one_or_none()
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account


async def get_owned_bank_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_db_user),
) -> BankAccount:
    return await get_bank_account_or_404(account_id, db, current_user)
