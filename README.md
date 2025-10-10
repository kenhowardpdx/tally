# Tally

Tally is an application designed to help you manage recurring bills and forecast your future bank account balance. With Tally, you can track upcoming payments, visualize your cash flow, and plan ahead with confidence.

## Architecture

Tally is built with a modern, cloud-native architecture:

- **Frontend**: Svelte application served via AWS CloudFront and S3
- **Backend**: Python FastAPI application running on AWS Lambda
- **Database**: PostgreSQL on AWS RDS
- **Authentication**: Auth0 integration
- **Infrastructure**: Managed with Terraform and AWS

## Development Options

### Option 1: Local Development with Docker Compose

For local development and testing:

## Getting Started with Docker Compose

Tally uses Docker Compose to simplify running all required services. Follow the steps below to get started:

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed
- [Docker Compose](https://docs.docker.com/compose/install/) installed

### Starting the Services

Start the services with:

```sh
docker-compose up
```

This command will build and start all necessary containers for Tally.

Access the application by opening your browser and navigating to [http://localhost:8000](http://localhost:8000) (or the port specified in your `docker-compose.yml`).

### Stopping the Services

To stop the services, press `Ctrl+C` in the terminal where Docker Compose is running, then run:

```sh
docker-compose down
```

## Configuration

You can customize environment variables and service settings in the `docker-compose.yml` file as needed.

### Option 2: AWS Cloud Infrastructure

For production deployment and cloud development:

#### Prerequisites

- AWS CLI with SSO configured
- Terraform >= 1.0.0
- Access to AWS account with appropriate permissions

#### Quick Start

```sh
# Navigate to infrastructure directory
cd infra

# Set up AWS credentials and initialize Terraform
make dev-setup

# Plan infrastructure changes
make plan

# Deploy infrastructure
make apply
```

For detailed infrastructure setup, deployment guides, and architecture documentation, see the [Infrastructure README](infra/README.md).

## Project Structure

```
├── backend/          # Python FastAPI backend
├── frontend/         # Svelte frontend application
├── infra/           # Terraform infrastructure as code
│   ├── modules/     # Reusable Terraform modules
│   ├── Makefile     # Infrastructure automation commands
│   └── README.md    # Detailed infrastructure documentation
└── scripts/         # Deployment and utility scripts
```

## Development Workflow

1. **Local Development**: Use Docker Compose for rapid development and testing
2. **Infrastructure**: Use Terraform with the provided Makefile for AWS deployment
3. **CI/CD**: GitHub Actions workflows for automated testing and deployment

## Support

For questions or issues, please open an issue on the [GitHub repository](https://github.com/kenhowardpdx/tally/issues).
