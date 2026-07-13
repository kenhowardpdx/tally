# Tally

Tally is a financial application for managing recurring bills and forecasting bank account balances.

## Tech Stack

- Backend: Python (FastAPI), SQLAlchemy (async) + Alembic, PostgreSQL (Neon in prod)
- Frontend: SvelteKit (Svelte 5), Tailwind CSS
- Auth: Auth0
- Infrastructure: Terraform (AWS)
- CI/CD: GitHub Actions, tested locally with [act](https://github.com/nektos/act)

## Getting Started

The whole stack (Postgres, backend, frontend) runs via Docker Compose:

```sh
docker compose up -d
cd backend && poetry run alembic upgrade head   # first run only
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000

See [backend/README.md](backend/README.md) and [frontend/README.md](frontend/README.md) for
running each service outside Docker (e.g. with hot-reload via `poetry run uvicorn --reload` or
`yarn dev` directly), and [docs/DEVELOPING.md](docs/DEVELOPING.md) for the full local
development guide, including testing GitHub Actions workflows locally with `act`.

## Documentation

- [Development Guide](docs/DEVELOPING.md)
- [Roadmap](docs/ROADMAP.md)
- [Operations](docs/OPERATIONS.md) — observability, backup/DR, cost, security, deployment
  audit, DNS decision, and the ops runbook
- [Branding](docs/BRANDING.md)
- [Infrastructure](infra/README.md)
