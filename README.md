
# Tally

Tally is a financial application for managing recurring bills and forecasting bank account balances.

## Tech Stack
- Backend: Python (FastAPI)
- Infrastructure: Terraform (AWS)
- CI/CD: GitHub Actions, tested locally with [act](https://github.com/nektos/act)

## Getting Started

1. Clone the repo
2. Install dependencies (see `docs/DEVELOPING.md`)
3. Run tests: `make test`

## Local Workflow Testing

We use [act](https://github.com/nektos/act) to run GitHub Actions locally. See [Development Guide](docs/DEVELOPING.md) for details.

## Documentation

- [Development Guide](docs/DEVELOPING.md)
- [Infrastructure](infra/README.md)
