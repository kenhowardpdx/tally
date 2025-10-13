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
- **Prefer rebase over merge commits**: Use `git rebase origin/main` instead of `git merge` to maintain clean history

#### Pull Request Creation
- **For complex PR descriptions**: Create `pr-body.md` file and use `gh pr create --body-file pr-body.md`
- **For simple PRs**: Use inline `--body` with GitHub CLI
- **Always clean up**: Remove `pr-body.md` after PR creation (it's temporary)
- **Use emojis and formatting**: Make PR descriptions clear and scannable with sections, checkboxes, and context

### GitHub Actions Version Management

- All GitHub Actions versions are centrally managed in `.github/action-versions.conf`
- Use `make validate-actions` to check that all workflows use approved versions
- Install git hooks with `make install-git-hooks` to automatically validate on commits
- Update `.github/action-versions.conf` when approving new action versions
- The validation script at `scripts/validate-actions.sh` enforces version consistency

#### Branch Management & Cleanup

- **Auto-prune setup**: Configure `git config --global fetch.prune true` for automatic cleanup
- **Regular pruning**: Use `git remote prune origin` to remove stale remote references
- **Local cleanup**: Delete merged branches with `git branch -d branch-name`
- **Force delete unmerged**: Use `git branch -D branch-name` for branches with open PRs
- **Verify cleanup**: Use `git branch -a` to check remaining branches

## Development Practices

### Local Development

- Use Docker Compose for local development environment
- **Use `.secrets` file** for local sensitive configuration (never commit this file)
- Test GitHub Actions locally using `act` (use Makefile targets like `make github_workflow_terraform-pr`)
- Validate Terraform changes locally before committing
- Run tests before pushing changes

#### .secrets File Pattern
Create a `.secrets` file in the project root for local development:
```bash
# .secrets file (never commit - already in .gitignore)
AWS_PROFILE=AdministratorAccess-123456789012
AWS_ROLE_ARN=arn:aws:iam::123456789012:role/tally-github-actions-role
TF_VAR_aws_account_id=123456789012
TF_VAR_aws_profile=AdministratorAccess-123456789012
```

Source it in your shell:
```bash
source .secrets
make github_workflow_terraform-pr  # Now has access to AWS credentials
```

### Testing

- Write unit tests for all business logic
- Use pytest fixtures for test setup
- Mock external dependencies in tests
- Aim for high test coverage
- Test both success and error scenarios

### Security

**🔒 CRITICAL: Never commit sensitive information to the repository.**

#### Sensitive Data Protection
- **Never commit secrets, API keys, tokens, or credentials** to any branch
- **Never commit real AWS account IDs, ARNs, or resource identifiers**
- **Never commit personal paths** (e.g., `/Users/username/`) - use generic placeholders
- **Use `.secrets` file** for local development configuration (already in .gitignore)
- **Use GitHub repository secrets** for CI/CD credentials
- **Use placeholder values** in documentation and examples (e.g., `123456789012` for AWS account IDs)

#### Configuration Management
- **Local Development**: Use `.secrets` file for sensitive configuration
- **GitHub Actions**: Use repository secrets (`${{ secrets.SECRET_NAME }}`)
- **Terraform**: Use variables and data sources, never hardcode sensitive values
- **Documentation**: Always use placeholder values, never real credentials

#### Code Examples - DO NOT DO:
```hcl
# ❌ NEVER DO THIS
bucket = "terraform-state-993450011441"  # Real account ID
profile = "AdministratorAccess-993450011441"  # Real account ID
```

#### Code Examples - CORRECT:
```hcl
# ✅ CORRECT - Use variables
bucket = "terraform-state-${var.aws_account_id}"
profile = var.aws_profile

# ✅ CORRECT - Placeholder in docs
bucket = "terraform-state-123456789012"  # Your AWS account ID
```

#### Emergency Response
If sensitive data is accidentally committed:
1. **DO NOT** push the commit
2. Use `git filter-repo` to clean history if already pushed
3. Contact GitHub Support if data is in PR history
4. Rotate any exposed credentials immediately

#### Additional Security Practices
- Follow AWS security best practices
- Use least privilege principle for IAM roles
- Validate all user inputs
- Enable comprehensive logging for security events
- Use environment variables for all configuration

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

## GitHub CLI and PR Management

### Accessing PR Comments and Reviews

When working with pull requests, use the GitHub CLI in non-interactive mode to access comments and reviews:

```bash
# View PR details without interactive prompts
TERM=dumb gh pr view <pr-number> --comments

# Get specific review/comment data using the API
gh api repos/owner/repo/pulls/<pr-number>/comments

# Extract specific comment details with jq
gh api repos/owner/repo/pulls/<pr-number>/comments | jq -r '.[] | "\(.path):\(.line) - \(.body)"'

# List PRs for current branch
gh pr list --head <branch-name>

# Get PR status information
gh pr status
```

### Copilot Review Comments

When Copilot provides review comments on PRs:
1. Use the API approach above to get specific line-by-line feedback
2. Address each comment systematically
3. Common issues Copilot flags:
   - Redundant code patterns
   - Formatting inconsistencies  
   - Accidental test/debug code
   - Security concerns
   - Performance optimizations

---

When suggesting code or infrastructure changes, please follow these guidelines and patterns to maintain consistency across the project.
