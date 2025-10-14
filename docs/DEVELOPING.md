# Development Guide

This guide helps you set up Tally for local development, workflow testing, and infrastructure management.

## Project Overview

Tally is a financial application for managing recurring bills and forecasting bank account balances. The backend is built with Python (FastAPI), infrastructure is managed with Terraform on AWS, and CI/CD is handled by GitHub Actions (locally tested with act).

## Prerequisites

- Python 3.13+
- Poetry
- Docker
- act
- AWS CLI

## First-time Setup

1. Clone the repo
2. Install Python dependencies: `poetry install`
3. Set up AWS credentials: `make -C infra aws-credentials`
4. Start Docker
5. Run tests: `make test`
6. Run workflows locally: `make github_workflow_terraform-pr`

## Security

- Never commit secrets or credentials.
- Use `.secrets` for sensitive values (already in `.gitignore`).

---

## Local GitHub Actions Testing with Act

[Act](https://github.com/nektos/act) is a tool that allows you to run GitHub Actions locally using Docker. This is incredibly useful for testing workflows before pushing changes and debugging CI/CD issues.

### Prerequisites

#### Install Act

**macOS (Homebrew):**

```bash
brew install act
```

**Other platforms:**

- Download from the [releases page](https://github.com/nektos/act/releases)
- Or use other package managers as documented in the [act repository](https://github.com/nektos/act#installation)

#### Install Docker

Act requires Docker to run the GitHub Actions containers:

- [Docker Desktop](https://docs.docker.com/desktop/) for macOS/Windows
- Docker Engine for Linux

### Quick Start

We've provided convenient Makefile targets to run workflows locally:

```bash
# Run the Terraform PR validation workflow
make github_workflow_terraform-pr

# Run the CI workflow
make github_workflow_ci

# List all available workflows
make list-workflows

# See all available make targets
make help
```

These Makefile targets automatically handle:

1. AWS credential mounting for workflows that need AWS access
2. Environment variable configuration
3. Proper act command construction
4. Error handling for missing workflows

### Manual Act Usage

You can also run act directly:

#### Run All Workflows

```bash
act
```

#### Run Specific Events

```bash
# Run workflows triggered by push events
act push

# Run workflows triggered by pull_request events
act pull_request
```

#### Run Specific Workflow Files

```bash
# Run a specific workflow file
act -W .github/workflows/ci.yml

# Run a specific workflow file with a specific event
act pull_request -W .github/workflows/terraform-pr.yml
```

#### Run Specific Jobs

```bash
# List all jobs
act -l

# Run a specific job
act -j backend-test
```

### Available Workflows

Our current GitHub Actions workflows:

#### 1. CI Workflow (`.github/workflows/ci.yml`)

- **Name:** CI
- **Triggers:** `push`, `pull_request` to `main` branch
- **Jobs:**
  - `backend-test`: Runs Python tests using Poetry
- **Local testing:**
  ```bash
  act push -W .github/workflows/ci.yml
  # or
  act pull_request -W .github/workflows/ci.yml
  ```

#### 2. Terraform PR Validation (`.github/workflows/terraform-pr.yml`)

- **Name:** Terraform PR Validation
- **Triggers:** `pull_request` to `main` branch (only when `infra/**` files change)
- **Jobs:**
  - `terraform-validate`: Validates Terraform configuration
- **Local testing:**
  ```bash
  act pull_request -W .github/workflows/terraform-pr.yml
  ```

### Act Configuration

#### Runner Images

Act uses Docker images to simulate GitHub's runner environments. You can specify which images to use:

Create a `.actrc` file in the project root:

```bash
# Use larger images for better compatibility (slower but more accurate)
-P ubuntu-latest=catthehacker/ubuntu:act-latest
-P ubuntu-22.04=catthehacker/ubuntu:act-22.04
-P ubuntu-20.04=catthehacker/ubuntu:act-20.04

# Or use smaller images for faster execution (may have compatibility issues)
# -P ubuntu-latest=catthehacker/ubuntu:act-latest-micro
```

#### AWS Credentials Setup

Before running any workflow locally, ensure your `~/.aws/credentials` file is in the correct INI format. Use the Makefile target:

```bash
make -C infra aws-credentials
```

This runs `scripts/export-aws-credentials.sh`, which logs in to AWS SSO using your profile from `.secrets` and exports credentials in the required INI format for Terraform, ACT, and AWS CLI.

Your `~/.aws/credentials` file should look like:

```ini
[default]
aws_access_key_id=...
aws_secret_access_key=...
aws_session_token=...
```

**Run this before any ACT or Makefile workflow targets.**

**Manual act usage:**

If running act directly, you can still use secrets and environment variables:

```bash
# Use a .secrets file (add to .gitignore!)
act --secret-file .secrets

# Or pass secrets via command line
act -s GITHUB_TOKEN=your_token_here

# Pass environment variables
act --env ENVIRONMENT=local
```

#### Event Payloads

You can provide custom event payloads for more realistic testing:

```bash
# Create a custom payload file
cat > push_payload.json << EOF
{
  "push": {
    "ref": "refs/heads/feature-branch",
    "repository": {
      "name": "tally",
      "owner": {
        "login": "kenhowardpdx"
      }
    }
  }
}
EOF

# Use the payload
act push --eventpath push_payload.json
```

### Troubleshooting

#### Common Issues

1. **Docker not running:**

   ```
   Error: Cannot connect to the Docker daemon
   ```

   - Solution: Start Docker Desktop or Docker Engine

2. **Permission denied:**

   ```
   Error: permission denied while trying to connect to Docker
   ```

   - Solution: Add your user to the docker group or run with sudo

3. **Workflow fails locally but passes on GitHub:**

   - Different runner environments
   - Try using larger/more compatible Docker images
   - Check for missing dependencies or different file paths

4. **Slow execution:**
   - Act downloads Docker images on first run
   - Use smaller images for faster execution
   - Consider using `--reuse` flag to reuse containers

#### Debugging Tips

1. **Verbose output:**

   ```bash
   act -v  # verbose
   act -vv # very verbose
   ```

2. **Dry run:**

   ```bash
   act --dry-run
   ```

3. **List available jobs and events:**

   ```bash
   act -l
   ```

4. **Keep containers for inspection:**
   ```bash
   act --rm=false
   # Then inspect with: docker ps -a
   ```

### Makefile Integration

We've integrated act testing into our Makefile for a streamlined developer experience:

#### Available Targets

```bash
# Export AWS credentials to ~/.aws/credentials
make aws-credentials

# List all available make targets
make help

# GitHub workflow testing
make github_workflow_terraform-pr   # Test Terraform PR validation
make github_workflow_ci             # Test CI workflow
make list-workflows                 # List all available workflows
```

#### How It Works

The Makefile uses a generic pattern that:

1. **Automatically mounts AWS credentials:** Uses your local `~/.aws` directory
2. **Configures AWS profile:** Automatically loads `AWS_PROFILE` from `.secrets` file
3. **Loads secrets:** Automatically uses `.secrets` file for sensitive values
4. **Sets required environment variables:** Configures regions and act-specific settings
5. **Validates workflow existence:** Shows helpful errors if workflow files don't exist
6. **Smart error handling:** Provides clear instructions if AWS_PROFILE is missing

#### Configuration

Create a `.secrets` file for sensitive values:

```bash
# .secrets (add to .gitignore)
AWS_PROFILE=YourAWSProfileName
AWS_ROLE_ARN=arn:aws:iam::123456789012:role/your-github-actions-role
```

Set your AWS profile environment variable:

```bash
# In your shell or .zshrc/.bashrc
export AWS_PROFILE=YourAWSProfileName

# Or set it per command
AWS_PROFILE=YourProfile make github_workflow_terraform-pr
```

## ACT vs CI/CD Workflow Logic

### How ACT/local and CI/CD are handled

Our workflows are designed to work seamlessly both locally (using ACT) and in CI/CD (GitHub Actions):

- **ACT/local runs:**

  - ACT automatically sets the `ACT` environment variable to `true`.
  - The workflow uses shell conditionals (`[ "$ACT" = "true" ]`) inside `run:` blocks to detect ACT/local runs.
  - AWS credentials are injected as environment variables by ACT, sourced from your local `~/.aws/credentials` and `.secrets` file.
  - The Makefile targets (`act-plan`, `act-apply`) mount your AWS credentials and source `.secrets` for ACT runs.
  - The backend is switched to local by running `make init-local`.

- **CI/CD runs:**
  - The workflow runs in GitHub Actions, where `ACT` is not set.
  - AWS credentials are configured using `aws-actions/configure-aws-credentials` and secrets from the repository.
  - The backend is switched to S3 by copying the backend config and running `terraform init -backend-config=backend.conf`.

### Credential Propagation

- For ACT/local, credentials are read from your local environment and injected by ACT.
- For CI/CD, credentials are provided via GitHub secrets and configured by the workflow.

### Backend Switching

- Local runs use a local backend to avoid S3 and AWS charges.
- CI/CD runs use the S3 backend for remote state management.

### Troubleshooting

- If ACT fails due to missing credentials, ensure your `~/.aws/credentials` and `.secrets` files are present and correctly formatted.
- If backend switching fails, use `make clean-terraform` to reset state and re-init.

### Example ACT Command

```bash
make act-plan  # Runs the Terraform PR workflow locally with proper credentials and backend
```

For more details, see the workflow and Makefile comments.

1. **Test locally before pushing:** Always run workflows locally to catch issues early
2. **Use Makefile targets:** `make github_workflow_*` provides the best experience with proper AWS setup
3. **Check resource usage:** Act can be resource-intensive; close unnecessary applications
4. **Version consistency:** Keep act updated to match GitHub's runner improvements
5. **Selective testing:** Use specific workflow targets to save time during development
6. **Keep secrets private:** Never commit the actual values in `.secrets` - use the commented examples

### Integration with Development Workflow

1. **Before committing changes:**

   ```bash
   # Test affected workflows using Makefile targets
   make github_workflow_terraform-pr  # If you changed infra files
   make github_workflow_ci            # If you changed backend code
   ```

2. **When modifying GitHub Actions:**

   ```bash
   # Test specific workflow using make target (preferred)
   make github_workflow_your-workflow-name

   # Or test directly with act
   act -W .github/workflows/your-workflow.yml
   ```

3. **Before creating pull requests:**

   ```bash
   # Run PR-triggered workflows
   make github_workflow_terraform-pr  # For infrastructure changes
   make github_workflow_ci            # For code changes

   # Or run all PR workflows manually
   act pull_request
   ```

### Accessing RDS PostgreSQL via Bastion Host

## Retrieve the Database Password

The RDS password is stored in AWS Secrets Manager:

```bash
aws secretsmanager get-secret-value --secret-id prod-rds-postgres-password --query 'SecretString' --output text
```

## Connect to the Bastion Host

1. Get the bastion host public IP from Terraform output or AWS Console.
2. SSH into the bastion host:

```bash
ssh -i /path/to/your-ssh-key.pem ec2-user@<bastion_public_ip>
```

## Connect to RDS from Bastion Host

Once on the bastion host, use psql or any PostgreSQL client:

```bash
psql -h <rds_endpoint> -U admin -d tally
```

- `<rds_endpoint>`: Get from Terraform output or AWS Console
- `admin`: Default username
- `tally`: Default database name
- Password: Retrieve from Secrets Manager as above

## SSH Port Forwarding (Optional)

To connect to RDS from your local machine via the bastion:

```bash
ssh -i /path/to/your-ssh-key.pem -L 5432:<rds_endpoint>:5432 ec2-user@<bastion_public_ip>
```

Then connect locally:

```bash
psql -h localhost -U admin -d tally
```

## Security Notes

- Bastion host should be stopped when not needed to minimize costs.
- Restrict SSH access to your IP in the bastion security group.
- Never expose RDS directly to the public internet.

### Additional Resources

- [Act Documentation](https://github.com/nektos/act)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Act Runner Images](https://github.com/catthehacker/docker_images)
- [Awesome Act](https://github.com/nektos/act#awesome-act) - Community resources

---

For questions or issues with local development, please check the existing issues or create a new one in the repository.
