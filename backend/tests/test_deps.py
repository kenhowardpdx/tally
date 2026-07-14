from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import get_current_user
from src.main import app
from src.models import User, UserDailyActivity
from tests.conftest import auth_as


def _login_as(sub: str) -> None:
    app.dependency_overrides[get_current_user] = auth_as(sub)


@pytest.fixture(autouse=True)
def _default_user():
    _login_as("auth0|activity_user")
    yield
    app.dependency_overrides.pop(get_current_user, None)


async def _get_user(db_session: AsyncSession, sub: str) -> User:
    result = await db_session.execute(select(User).where(User.auth0_sub == sub))
    return result.scalar_one()


async def _daily_activity_rows(db_session: AsyncSession, user_id: int) -> list[UserDailyActivity]:
    result = await db_session.execute(
        select(UserDailyActivity).where(UserDailyActivity.user_id == user_id)
    )
    return list(result.scalars().all())


async def test_first_request_records_activity(client: AsyncClient, db_session: AsyncSession):
    await client.get("/api/v1/me/consent")

    user = await _get_user(db_session, "auth0|activity_user")
    assert user.last_active_at is not None

    rows = await _daily_activity_rows(db_session, user.id)
    assert len(rows) == 1
    assert rows[0].activity_date == user.last_active_at.date()


async def test_repeat_request_within_throttle_does_not_duplicate(
    client: AsyncClient, db_session: AsyncSession
):
    await client.get("/api/v1/me/consent")
    user = await _get_user(db_session, "auth0|activity_user")
    first_seen = user.last_active_at

    await client.get("/api/v1/me/consent")
    db_session.expire_all()
    user = await _get_user(db_session, "auth0|activity_user")
    assert user.last_active_at == first_seen
    assert len(await _daily_activity_rows(db_session, user.id)) == 1


async def test_request_after_throttle_window_records_again(
    client: AsyncClient, db_session: AsyncSession
):
    await client.get("/api/v1/me/consent")
    user = await _get_user(db_session, "auth0|activity_user")

    # Simulate the hourly throttle window having elapsed.
    user.last_active_at = datetime.now(UTC) - timedelta(hours=2)
    await db_session.commit()

    await client.get("/api/v1/me/consent")
    db_session.expire_all()
    user = await _get_user(db_session, "auth0|activity_user")
    assert user.last_active_at > datetime.now(UTC) - timedelta(minutes=1)
    assert len(await _daily_activity_rows(db_session, user.id)) == 1
