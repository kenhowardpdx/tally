# Tally Backend

A backend API built with [FastAPI](https://fastapi.tiangolo.com/) to manage bills and forecast bank balances.

## Getting Started

### Install Dependencies

```bash
poetry install
```

### Local Database

```bash
cp .env.example .env          # then fill in AUTH0_DOMAIN/AUTH0_AUDIENCE once a tenant exists
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
