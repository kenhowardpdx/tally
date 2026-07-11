from src.core.config import Settings


def test_normalizes_plain_postgresql_scheme_to_asyncpg():
    settings = Settings(database_url_readwrite="postgresql://user:pass@host/db")
    assert settings.database_url_readwrite == "postgresql+asyncpg://user:pass@host/db"


def test_leaves_already_asyncpg_scheme_unchanged():
    url = "postgresql+asyncpg://user:pass@host/db"
    settings = Settings(database_url_readwrite=url)
    assert settings.database_url_readwrite == url


def test_translates_sslmode_to_ssl_and_drops_channel_binding():
    # Exactly the shape Neon's console hands out - psycopg2/libpq query
    # params that asyncpg's connect() doesn't accept as keyword arguments.
    settings = Settings(
        database_url_readwrite=(
            "postgresql://user:pass@ep-example-pooler.neon.tech/db"
            "?sslmode=require&channel_binding=require"
        )
    )
    assert settings.database_url_readwrite == (
        "postgresql+asyncpg://user:pass@ep-example-pooler.neon.tech/db?ssl=require"
    )
