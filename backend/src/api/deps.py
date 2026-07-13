from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import get_current_user
from src.core.database import get_db
from src.models import BankAccount, User, UserDailyActivity

# Throttle for last_active_at/user_daily_activity writes - avoids a write on
# every single authenticated request while still giving MAU/DAU/stale-account
# queries hour-granularity freshness.
_ACTIVITY_THROTTLE = timedelta(hours=1)


async def _record_activity(user: User, db: AsyncSession) -> None:
    now = datetime.now(timezone.utc)
    if user.last_active_at is not None and now - user.last_active_at < _ACTIVITY_THROTTLE:
        return
    user.last_active_at = now
    await db.execute(
        insert(UserDailyActivity)
        .values(user_id=user.id, activity_date=now.date())
        .on_conflict_do_nothing(index_elements=["user_id", "activity_date"])
    )
    await db.commit()


async def get_current_db_user(
    request: Request,
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

    if user is None:
        user = User(auth0_sub=auth0_sub, email=claims.get("email"))
        db.add(user)
        await db.commit()
        await db.refresh(user)

    await _record_activity(user, db)
    # Read by log_requests (backend/src/core/logging.py) after the route
    # handler returns, so the access log can attribute a request to a user
    # without a second JWT decode in the middleware.
    request.state.user_id = user.id
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
