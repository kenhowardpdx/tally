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

## Local GitHub Actions Testing

Tally includes support for testing GitHub Actions workflows locally using [Act](https://github.com/nektos/act). This allows you to validate workflows before pushing changes.

### Quick Setup

1. **Install Act**:

   ```sh
   # macOS
   brew install act

   # Or download from: https://github.com/nektos/act/releases
   ```

2. **Configure Secrets**:

   ```sh
   # Copy the example secrets file
   cp .secrets.example .secrets

   # Edit .secrets with your actual values
   # AWS_PROFILE: Your AWS profile name from ~/.aws/config
   # AWS_ROLE_ARN: Your GitHub Actions role ARN
   # TF_VAR_aws_account_id: Your AWS account ID (for Terraform)
   # TF_VAR_aws_profile: Your AWS profile (for local Terraform)
   ```

3. **Test Workflows**:

   ```sh
   # The Makefile will automatically use AWS_PROFILE from .secrets
   # List available workflow targets
   make help

   # Test Terraform PR validation
   make github_workflow_terraform-pr

   # Test CI workflow
   make github_workflow_ci
   ```

### Secrets Configuration

The `.secrets` file contains **required** configuration for local development:

- **AWS_PROFILE**: Your AWS SSO profile name (e.g., `AdministratorAccess-123456789012`) - **Required**
- **AWS_ROLE_ARN**: The IAM role ARN that GitHub Actions uses (e.g., `arn:aws:iam::123456789012:role/tally-github-actions-role`)
- **TF_VAR_aws_account_id**: Your AWS account ID for Terraform backend configuration - **Required**
- **TF_VAR_aws_profile**: Your AWS profile for local Terraform operations - **Required**

**GitHub Actions**: Uses repository secrets (`AWS_ACCOUNT_ID`, `AWS_ROLE_ARN`) instead of the `.secrets` file.

**Important**: 
- The `.secrets` file is included in `.gitignore` and should never be committed to version control
- Required variables must be set - commands will fail with clear error messages if missing

## Development Workflow

1. **Local Development**: Use Docker Compose for rapid development and testing
2. **Infrastructure**: Use Terraform with the provided Makefile for AWS deployment
3. **CI/CD**: GitHub Actions workflows for automated testing and deployment
4. **Local Testing**: Use Act with our Makefile targets to test workflows locally

For detailed development practices, local testing with GitHub Actions, and debugging guides, see the [Development Guide](docs/DEVELOPING.md).

## Support

For questions or issues, please open an issue on the [GitHub repository](https://github.com/kenhowardpdx/tally/issues).
# Test comment
