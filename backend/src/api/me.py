from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_db_user
from src.core.database import get_db
from src.models import User
from src.schemas.user import ConsentStatus

router = APIRouter(prefix="/api/v1/me", tags=["me"])


def _consent_status(user: User) -> ConsentStatus:
    return ConsentStatus(
        terms_accepted=user.terms_accepted_at is not None,
        terms_accepted_at=user.terms_accepted_at,
    )


@router.get("/consent", response_model=ConsentStatus)
async def get_consent(current_user: User = Depends(get_current_db_user)) -> ConsentStatus:
    return _consent_status(current_user)


@router.post("/consent", response_model=ConsentStatus)
async def accept_consent(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_db_user),
) -> ConsentStatus:
    # Idempotent: accepting again (e.g. a duplicate click, or the frontend
    # re-posting after a network retry) keeps the original acceptance
    # timestamp rather than bumping it forward.
    if current_user.terms_accepted_at is None:
        current_user.terms_accepted_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(current_user)
    return _consent_status(current_user)
