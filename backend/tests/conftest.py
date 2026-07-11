from collections.abc import AsyncGenerator, Callable

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.core.auth import get_current_user
from src.core.config import settings
from src.core.database import Base, get_db
from src.main import app

# NullPool: every connection is opened fresh and discarded rather than
# reused from a pool. pytest-asyncio gives each async test its own event
# loop by default, and asyncpg connections can't be reused across loops (or
# even safely reused concurrently within one) - pooling here risks handing a
# later test a connection still tied to a prior test's loop/transaction state.
test_engine = create_async_engine(settings.database_url_readwrite, poolclass=NullPool)


@pytest_asyncio.fixture(autouse=True)
async def _schema() -> AsyncGenerator[None, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    # Each test runs inside an outer transaction that's rolled back at
    # teardown, even though route handlers call db.commit() themselves -
    # join_transaction_mode="create_savepoint" turns those commits into
    # SAVEPOINTs nested inside the outer (uncommitted) transaction, so
    # nothing persists across tests.
    connection = await test_engine.connect()
    outer_transaction = await connection.begin()
    session_factory = async_sessionmaker(
        bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint"
    )
    session = session_factory()

    yield session

    await session.close()
    await outer_transaction.rollback()
    await connection.close()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


def auth_as(sub: str, email: str | None = None) -> Callable[[], dict]:
    """Overrides get_current_user so a test can act as a given Auth0 subject
    without a real token - assign to app.dependency_overrides[get_current_user]."""

    def _claims() -> dict:
        return {"sub": sub, "email": email}

    return _claims


__all__ = ["auth_as", "get_current_user"]
