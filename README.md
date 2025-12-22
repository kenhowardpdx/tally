# Tally

Tally is a financial application for managing recurring bills and forecasting bank account balances.

## Tech Stack

- Backend: Python (FastAPI)
- Infrastructure: Terraform (AWS)
- CI/CD: GitHub Actions, tested locally with [act](https://github.com/nektos/act)

## Getting Started

### Backend Development

1. Clone the repo
2. Install dependencies (see [Development Guide](docs/DEVELOPING.md))
3. Run tests: `cd backend && poetry run pytest`

### Infrastructure Development

1. Configure AWS SSO profile (see [Local Terraform Development](docs/LOCAL-TERRAFORM-DEV.md))
2. Create `.secrets` file from `.secrets.example`
3. Initialize: `cd infra && make local-init`
4. Plan changes: `make local-plan`
5. Apply: `make local-apply`

See [Local Terraform Development Guide](docs/LOCAL-TERRAFORM-DEV.md) for detailed workflow.

## Local Workflow Testing

We use [act](https://github.com/nektos/act) to run GitHub Actions locally. See [Development Guide](docs/DEVELOPING.md) for details.

## Documentation

- [Development Guide](docs/DEVELOPING.md)
- [Local Terraform Development](docs/LOCAL-TERRAFORM-DEV.md)
- [Infrastructure](infra/README.md)
- [Cost Optimization](docs/cost-optimization.md)
