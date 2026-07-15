from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.core.config import settings

# pool_pre_ping + pool_recycle: the engine is created once at module scope
# and its pooled connections survive across warm Lambda invocations. Neon
# closes idle connections well under our recycle window, so without these a
# request landing on a container whose pooled connection went stale gets
# `asyncpg.exceptions.InterfaceError: connection is closed` instead of a
# transparent reconnect.
engine = create_async_engine(
    settings.database_url_readwrite,
    pool_pre_ping=True,
    pool_recycle=270,
)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
