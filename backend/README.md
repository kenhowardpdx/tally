# Tally Backend

A backend API built with [FastAPI](https://fastapi.tiangolo.com/) to manage bills and forecast bank balances.

To run the whole stack (Postgres, backend, frontend) together instead, use
`docker compose up -d` from the repo root — see the root [README](../README.md).

## Getting Started

### Install Dependencies

```bash
poetry install
```

### Local Database

```bash
cp .env.example .env          # fill in AUTH0_DOMAIN/AUTH0_AUDIENCE from your Auth0 tenant/API
docker compose up -d postgres # from the repo root; runs on host port 5433
poetry run alembic upgrade head
```

### Run the Application

```bash
poetry run uvicorn src.main:app --reload
```

### Run Tests

```bash
poetry run pytest
```
