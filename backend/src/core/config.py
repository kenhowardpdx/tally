from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Named to match infra/modules/lambda/main.tf's Lambda environment variable
    # (DATABASE_URL_READWRITE) - the app doesn't do read/write splitting yet, so
    # there's no use of the read-only replica URL Terraform also sets.
    database_url_readwrite: str = "postgresql+asyncpg://tally:tally@localhost:5433/tally"

    auth0_domain: str = ""
    auth0_audience: str = ""


settings = Settings()
