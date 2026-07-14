# Development Guide

This guide helps you set up Tally for local development, workflow testing, and infrastructure management.

## Project Overview

Tally is a financial application for managing recurring bills and forecasting bank account balances. The backend is Python (FastAPI + SQLAlchemy/Alembic), the frontend is SvelteKit (Svelte 5), infrastructure is managed with Terraform on AWS, and CI/CD is handled by GitHub Actions (locally tested with act).

## Prerequisites

- Python 3.13+ and Poetry (backend)
- Node.js >=20.19 (or >=22.12, or >=24) and Yarn (frontend) — `.nvmrc` floats to the current LTS
- Docker (Postgres locally, or the whole stack via Docker Compose)
- AWS CLI, act (only needed for infrastructure/CI work — see below)

## First-time Setup

1. Clone the repo
2. `cp backend/.env.example backend/.env` and `cp frontend/.env.example frontend/.env`, then
   fill in the Auth0 values from your tenant/SPA application (see [Local Application
   Development](#local-application-development) below)
3. Start Docker and run `docker compose up -d`
4. Apply database migrations: `cd backend && poetry run alembic upgrade head`
5. Run tests: `cd backend && poetry run pytest` and `cd frontend && yarn test`

Steps 3-5 are only needed once (and again whenever new migrations land). Everything past this
point — Terraform, AWS SSO, and `act` — is for infrastructure/CI work, not day-to-day app
development.

## Local Application Development

The full stack (Postgres, backend, frontend) runs via Docker Compose from the repo root:

```bash
docker compose up -d
cd backend && poetry run alembic upgrade head   # first run, and after new migrations
```

- Frontend: http://localhost:5173 (hot-reloads — the frontend container bind-mounts the
  source tree)
- Backend: http://localhost:8000

To run either service outside Docker instead (e.g. for a debugger), see `backend/README.md`
and `frontend/README.md`.

### Auth0

Both services need real Auth0 values before login works:

- `backend/.env`: `AUTH0_DOMAIN`, `AUTH0_AUDIENCE` — from the Auth0 tenant and the API you
  registered there.
- `frontend/.env`: `PUBLIC_AUTH0_DOMAIN`, `PUBLIC_AUTH0_CLIENT_ID`, `PUBLIC_AUTH0_AUDIENCE` —
  from the Auth0 SPA application. Add `http://localhost:5173` as an Allowed Callback/Logout/Web
  Origin URL in that application's settings.

### `.secrets` vs. `backend/.env` / `frontend/.env`

These serve different purposes and both are needed — one isn't a replacement for the other:

- **`backend/.env`, `frontend/.env`**: runtime configuration for the *application itself*
  (database URL, Auth0 values). Read directly by the backend/frontend processes, whether run
  locally or in Docker Compose. Not used by Terraform or CI.
- **`.secrets`** (repo root): credentials for *infrastructure and CI tooling* — AWS SSO
  profile/role and Terraform variables (`TF_VAR_*`, including the Neon connection strings and
  Auth0 values Terraform passes to Lambda). Used by `make` targets, `act` (local GitHub Actions
  runs), and direct `terraform` commands. Not read by the running application. Copy
  `.secrets.example` to get started; see [Configuration](#configuration) below for the minimum
  required values.

## Security

- Never commit secrets or credentials.
- Use `.secrets` for infra/CI values and `backend/.env`/`frontend/.env` for app config (already
  in `.gitignore`).

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

There are two auth targets depending on what you're doing:

| Target | When to use |
|--------|-------------|
| `make aws-login` | Direct terraform use (`terraform plan`, `terraform validate`, etc.) |
| `make aws-creds` | Before running ACT workflows (`make github_workflow_*`) |

`aws-login` does an SSO login only — Terraform reads the SSO session directly via `AWS_PROFILE`. No credential export needed.

`aws-creds` does the same SSO login, then exports static STS credentials to `~/.aws/credentials` and updates the credential vars in `.secrets` (preserving everything else). Run this before ACT since containers can't use SSO.

**Credentials expire after ~8 hours. Re-run the appropriate target when they do.**

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
# Authenticate with AWS SSO (for direct terraform)
make aws-login

# Authenticate + export static credentials (for ACT)
make aws-creds

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

Uses the same `.secrets` file in the project root described under [Security](#security) above
(copy `.secrets.example` to get started) — there should only ever be one, never a second copy
under `infra/`. At minimum it needs:

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

### Accessing the Production Database (Neon)

Production uses [Neon](https://neon.tech) (managed Postgres), not RDS — there's no bastion host
or VPC hop needed. The Neon project/database is created and managed manually (not
Terraform-managed; see the "Neon: manual vs. Terraform-managed" decision in
[docs/ROADMAP.md](ROADMAP.md)).

Connect directly with the connection string from the Neon console (or from `.secrets`'
`TF_VAR_database_url_readwrite`/`TF_VAR_database_url_readonly`, which use the same value):

```bash
psql "postgresql://user:password@ep-example-pooler.us-west-2.aws.neon.tech/dbname?sslmode=require"
```

Treat production data with care — prefer the read-only connection string for anything that
isn't an intentional write.

### Additional Resources

- [Act Documentation](https://github.com/nektos/act)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Act Runner Images](https://github.com/catthehacker/docker_images)
- [Awesome Act](https://github.com/nektos/act#awesome-act) - Community resources

---

For questions or issues with local development, please check the existing issues or create a new one in the repository.
