# GitHub Copilot Instructions

This file provides context and guidelines for GitHub Copilot when working on the Tally project.

## Project Overview

Tally is a financial application for managing recurring bills and forecasting bank account balances. The architecture consists of:

- **Backend**: Python FastAPI application deployed on AWS Lambda
- **Frontend**: Svelte application (planned) served via AWS CloudFront and S3
- **Database**: PostgreSQL on AWS RDS
- **Authentication**: Auth0 integration
- **Infrastructure**: Terraform for AWS resource management

## Code Style and Conventions

### Python (Backend)

- Use Python 3.13+ features
- Follow PEP 8 style guidelines
- Use type hints for all function signatures
- Prefer Poetry for dependency management
- Use pytest for testing
- Follow FastAPI best practices for API development
- Use Pydantic models for request/response validation

### Infrastructure (Terraform)

- Use Terraform >= 1.0.0
- Organize code into reusable modules
- Follow HashiCorp Configuration Language (HCL) best practices
- Use variables.tf and outputs.tf for module interfaces
- Include comprehensive resource tagging
- Use data sources for existing resources when possible

### Git Workflow

- Use conventional commits format (feat:, fix:, docs:, etc.)
- Create feature branches from main
- Use descriptive branch names (feature/description, fix/bug-name)
- Include tests for new features
- Update documentation when adding new functionality

## Development Practices

### Local Development

- Use Docker Compose for local development environment
- Test GitHub Actions locally using `act` (use Makefile targets like `make github_workflow_terraform-pr`)
- Validate Terraform changes locally before committing
- Run tests before pushing changes

### Testing

- Write unit tests for all business logic
- Use pytest fixtures for test setup
- Mock external dependencies in tests
- Aim for high test coverage
- Test both success and error scenarios

### Security

- Never commit secrets or sensitive data
- Use environment variables for configuration
- Follow AWS security best practices
- Use least privilege principle for IAM roles
- Validate all user inputs

## Project Structure

```
├── backend/          # Python FastAPI application
│   ├── src/         # Source code
│   ├── tests/       # Test files
│   ├── pyproject.toml # Poetry configuration
│   └── Dockerfile   # Container configuration
├── infra/           # Terraform infrastructure
│   ├── modules/     # Reusable Terraform modules
│   ├── main.tf      # Main infrastructure configuration
│   └── Makefile     # Infrastructure automation
├── scripts/         # Utility scripts
├── docs/           # Documentation
└── .github/        # GitHub configuration and workflows
```

## Common Patterns

### FastAPI Route Structure

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1", tags=["resource"])

class ResourceRequest(BaseModel):
    name: str
    value: int

class ResourceResponse(BaseModel):
    id: int
    name: str
    value: int

@router.post("/resources", response_model=ResourceResponse)
async def create_resource(request: ResourceRequest):
    # Implementation here
    pass
```

### Terraform Module Structure

```hcl
# variables.tf
variable "environment" {
  description = "Environment name"
  type        = string
}

# main.tf
resource "aws_lambda_function" "api" {
  function_name = "${var.environment}-tally-api"
  # ... other configuration

  tags = {
    Environment = var.environment
    Project     = "tally"
  }
}

# outputs.tf
output "function_arn" {
  description = "Lambda function ARN"
  value       = aws_lambda_function.api.arn
}
```

### Error Handling

```python
from fastapi import HTTPException

# Use appropriate HTTP status codes
raise HTTPException(
    status_code=404,
    detail="Resource not found"
)

# Log errors appropriately
import logging
logger = logging.getLogger(__name__)
logger.error("Error processing request", exc_info=True)
```

## Environment-Specific Guidelines

### Development

- Use local PostgreSQL via Docker Compose
- Enable debug logging
- Use development-specific configuration
- Mock external services when possible

### Production

- Use AWS RDS for PostgreSQL
- Enable comprehensive logging and monitoring
- Use production-grade security configurations
- Implement proper error handling and recovery

## Dependencies and Tools

### Backend Dependencies

- FastAPI: Web framework
- Pydantic: Data validation
- SQLAlchemy: ORM (if needed)
- pytest: Testing framework
- Poetry: Dependency management

### Infrastructure Tools

- Terraform: Infrastructure as Code
- AWS CLI: AWS operations
- act: Local GitHub Actions testing
- Docker: Containerization

## Documentation Requirements

- Update README.md for user-facing changes
- Update docs/DEVELOPING.md for development process changes
- Include docstrings for all public functions and classes
- Document API endpoints with FastAPI automatic documentation
- Include examples in documentation

## GitHub Actions Workflows

### CI Workflow

- Runs on push/PR to main
- Executes backend tests
- Validates code formatting

### Terraform PR Validation

- Runs on PRs affecting infra/ directory
- Validates Terraform configuration
- Checks formatting and runs terraform plan

Use `make github_workflow_terraform-pr` to test workflows locally before pushing.

---

When suggesting code or infrastructure changes, please follow these guidelines and patterns to maintain consistency across the project.
