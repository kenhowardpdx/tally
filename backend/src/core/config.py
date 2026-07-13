from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

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

    # Skips real Auth0 token validation entirely and JIT-provisions a fixed
    # dummy user (see get_current_user) - lets `docker compose up` be
    # exercised end-to-end without a real Auth0 login. Off by default; must
    # never be set in a deployed environment (nothing in infra/ sets this).
    dev_auth_bypass: bool = False

    # Structured (JSON) logging level - see src/core/logging.py. INFO logs one
    # line per request (method/path/status/duration); DEBUG adds library
    # internals (SQLAlchemy, httpx) that are noisy for routine operation.
    log_level: str = "INFO"

    @field_validator("database_url_readwrite")
    @classmethod
    def _normalize_for_asyncpg(cls, value: str) -> str:
        # Neon's console (and most Postgres providers) hand out standard libpq-
        # style connection strings - a few adjustments make them work with the
        # asyncpg driver instead:
        #   - scheme needs the +asyncpg suffix, or SQLAlchemy defaults to the
        #     sync psycopg2 driver (not installed here).
        #   - sslmode= is psycopg2/libpq's name for what asyncpg calls ssl= -
        #     passed through verbatim, asyncpg's connect() rejects the
        #     unrecognized "sslmode" kwarg outright.
        #   - channel_binding= has no asyncpg equivalent at all (it negotiates
        #     channel binding automatically as part of SCRAM auth) - same
        #     unrecognized-kwarg rejection, so it just gets dropped.
        parts = urlsplit(value)
        scheme = "postgresql+asyncpg" if parts.scheme == "postgresql" else parts.scheme

        query_params = [
            ("ssl" if key == "sslmode" else key, val)
            for key, val in parse_qsl(parts.query, keep_blank_values=True)
            if key != "channel_binding"
        ]

        return urlunsplit(
            (scheme, parts.netloc, parts.path, urlencode(query_params), parts.fragment)
        )


settings = Settings()
