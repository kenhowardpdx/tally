from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Named to match infra/modules/lambda/main.tf's Lambda environment variable
    # (DATABASE_URL_READWRITE) - the app doesn't do read/write splitting yet, so
    # there's no use of the read-only replica URL Terraform also sets.
    database_url_readwrite: str = "postgresql+asyncpg://tally:tally@localhost:5433/tally"

    auth0_domain: str = ""
    auth0_audience: str = ""

    @field_validator("database_url_readwrite")
    @classmethod
    def _use_asyncpg_driver(cls, value: str) -> str:
        # Neon's console (and most Postgres providers) hand out plain
        # postgresql:// connection strings - create_async_engine needs the
        # +asyncpg driver suffix or it falls back to psycopg2 (sync, and not
        # even installed here). Normalize rather than relying on whoever sets
        # the secret to remember to add the suffix themselves.
        if value.startswith("postgresql://"):
            return "postgresql+asyncpg://" + value.removeprefix("postgresql://")
        return value


settings = Settings()
