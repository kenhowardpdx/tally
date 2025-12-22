# Local Terraform Development Guide

This guide explains how to develop and test Tally infrastructure changes locally while keeping GitHub Actions workflows working perfectly.

## Table of Contents

- [Quick Start](#quick-start)
- [How It Works](#how-it-works)
- [Common Workflows](#common-workflows)
- [Workspace Strategy](#workspace-strategy)
- [Troubleshooting](#troubleshooting)

## Quick Start

### 1. Configure AWS SSO Profile

Ensure you have an AWS SSO profile configured in `~/.aws/config`:

```ini
[profile AdministratorAccess-123456789012]
sso_start_url = https://your-org.awsapps.com/start
sso_region = us-east-1
sso_account_id = 123456789012
sso_role_name = AdministratorAccess
region = us-west-2
```

### 2. Create Local Configuration

Copy the example secrets file and configure it:

```bash
cp .secrets.example .secrets
```

Edit `.secrets` with your actual values:

```bash
# Minimum required for local development
AWS_PROFILE=AdministratorAccess-123456789012
TF_VAR_aws_account_id=123456789012
```

### 3. Initialize and Plan

```bash
cd infra
make local-init   # Initialize Terraform with S3 backend + local-dev workspace
make local-plan   # See what changes would be made
```

### 4. Apply Changes (Optional)

```bash
make local-apply  # Apply changes to the local-dev workspace
```

### 5. Clean Up When Done

```bash
make local-destroy  # Destroy all infrastructure in local-dev workspace
```

## How It Works

### Workspace Isolation

The local development setup uses **Terraform workspaces** to completely isolate your local experiments from production:

- **`default` workspace**: Used by GitHub Actions for production deployments (TF_VAR_environment=prod)
- **`local-dev` workspace**: Your personal sandbox for testing changes (TF_VAR_environment=dev)

Both workspaces use the **same S3 backend**, but maintain separate state files:

- Production: `s3://terraform-state-123456789012/env:/default/tally/prod/terraform.tfstate`
- Local dev: `s3://terraform-state-123456789012/env:/local-dev/tally/prod/terraform.tfstate`

### Environment-Aware Infrastructure

Each workspace creates **completely separate infrastructure** using the `TF_VAR_environment` variable:

**Local-dev workspace (TF_VAR_environment=dev):**

- Lambda: `tally-dev-backend`
- API Gateway stage: `/dev`
- CloudFront: Auto-generated domain with origin_path `/dev`
- Neon branch: `development`
- S3 buckets: `tally-frontend-dev-123456789012`, `tally-backend-dev-123456789012-us-west-2`
- No custom domain (CloudFront only)

**Default workspace (TF_VAR_environment=prod):**

- Lambda: `tally-prod-backend`
- API Gateway stage: `/prod`
- CloudFront: Custom domain `tally.kenhoward.dev` with origin_path `/prod`
- Neon branch: `production`
- S3 buckets: `tally-frontend-prod-123456789012`, `tally-backend-prod-123456789012-us-west-2`
- ACM certificate and Route53 DNS (prod only)

### Shared Resources

Only these resources are shared between environments:

- **Neon project**: `example-project-12345678` (but different branches per environment)
- **S3 backend bucket**: Same bucket, different state files per workspace

This means:

- ✅ You can deploy real infrastructure to test your changes
- ✅ Your changes won't affect production until merged to main
- ✅ You can safely destroy everything in local-dev without affecting production
- ✅ GitHub Actions workflows remain unchanged and work as before

### Authentication Flow

**Local Development:**

1. `scripts/tf-local` script wraps Terraform commands
2. Uses AWS SSO profile authentication (no credential exports needed)
3. Automatically checks SSO session and prompts for login if expired
4. Sets proper environment variables for Terraform

**GitHub Actions:**

1. Uses OIDC authentication with AWS (no credentials stored)
2. Assumes the `tally-github-actions-role` IAM role
3. Uses `default` workspace for production deployments

### File Structure

```
.secrets                    # Your local config (gitignored)
scripts/
  tf-local                  # Local development wrapper script
  export-aws-credentials.sh # Export SSO creds for ACT testing
  setup-aws.sh             # Legacy SSO setup (deprecated)
infra/
  backend.conf              # S3 backend template
  Makefile                  # Convenient make targets
  main.tf                   # Infrastructure configuration
```

## Common Workflows

### Testing a New Module

```bash
# 1. Create your new module
vim infra/modules/my-new-module/main.tf

# 2. Add the module to main.tf
vim infra/main.tf

# 3. Plan the changes
make local-plan

# 4. Apply to test in local-dev workspace
make local-apply

# 5. Test the deployed infrastructure
# ... your testing ...

# 6. Destroy when done
make local-destroy

# 7. Push to GitHub
git add infra/
git commit -m "feat: add new module"
git push
```

### Testing Infrastructure Changes

```bash
# 1. Make your changes
vim infra/modules/vpc/main.tf

# 2. Format code
make local-fmt

# 3. Validate syntax
make local-validate

# 4. Plan changes
make local-plan

# 5. Apply if looks good
make local-apply

# 6. Verify changes
make local-state  # List all resources

# 7. When satisfied, push to GitHub
git push origin feature/my-changes
```

### Complete Teardown and Rebuild

```bash
# Destroy everything in local-dev
make local-destroy

# Clean local Terraform files
make clean-terraform

# Reinitialize
make local-init

# Rebuild infrastructure
make local-apply
```

### Switching Between Workspaces

```bash
# Show current workspace
make local-workspace

# Switch manually if needed
cd infra
../scripts/tf-local workspace select default  # Production (read-only for you)
../scripts/tf-local workspace select local-dev # Your development workspace
```

## Workspace Strategy

### Best Practices

1. **Never apply changes to `default` workspace locally**

   - This is production and managed by GitHub Actions
   - You can view its state, but don't modify it

2. **Use `local-dev` for all testing**

   - Deploy real infrastructure to test
   - Experiment freely
   - Destroy when done to avoid costs

3. **Keep local-dev in sync with main**

   - Regularly destroy and rebuild to match production
   - This catches configuration drift

4. **Use environment variable for logical separation**
   - Local: `TF_VAR_environment=dev` (default)
   - Production: `TF_VAR_environment=prod` (GitHub Actions)
   - This affects resource naming: `tally-dev-*` vs `tally-prod-*`

### Cost Management

Since `local-dev` deploys real AWS resources:

- ✅ **DO** destroy resources when done testing: `make local-destroy`
- ✅ **DO** use smaller instance sizes for testing (modify variables locally)
- ✅ **DO** monitor costs in AWS Cost Explorer
- ❌ **DON'T** leave local-dev infrastructure running overnight
- ❌ **DON'T** deploy expensive resources (large RDS instances, NAT gateways) unless necessary

### Viewing Production State

To inspect production state without modifying it:

```bash
cd infra
../scripts/tf-local workspace select default
../scripts/tf-local state list
../scripts/tf-local show
../scripts/tf-local workspace select local-dev  # Switch back
```

## Troubleshooting

### AWS SSO Session Expired

**Error:**

```
Error: failed to refresh cached credentials
```

**Solution:**
The `tf-local` script automatically detects and prompts for SSO login. If it doesn't:

```bash
aws sso login --profile AdministratorAccess-123456789012
```

### Backend Initialization Fails

**Error:**

```
Error: Failed to get existing workspaces: S3 bucket does not exist
```

**Solution:**
The S3 state bucket needs to be created first. This should exist from initial setup, but if not:

```bash
aws s3 mb s3://terraform-state-$TF_VAR_aws_account_id --profile $AWS_PROFILE
aws s3api put-bucket-versioning \
  --bucket terraform-state-$TF_VAR_aws_account_id \
  --versioning-configuration Status=Enabled \
  --profile $AWS_PROFILE
```

### Wrong Workspace

**Error:**

```
⚠️  This will apply changes to AWS infrastructure
Workspace: default
```

**Solution:**
You're in the production workspace! Switch to local-dev:

```bash
../scripts/tf-local workspace select local-dev
```

### Clean Slate Needed

If Terraform state gets corrupted or you want to start fresh:

```bash
make clean-terraform  # Remove all local Terraform files
make local-init       # Reinitialize
```

### ACT Testing (GitHub Actions Locally)

To test GitHub Actions workflows locally with ACT, you need temporary AWS credentials:

```bash
# Export SSO credentials to .secrets
./scripts/export-aws-credentials.sh

# Test PR workflow
cd infra
make act-plan

# Test apply workflow (use caution!)
make act-apply
```

**Note:** ACT testing uses temporary credentials that expire. You'll need to re-run `export-aws-credentials.sh` periodically.

### Neon API Key

If you're using Neon database modules, set the API key:

```bash
# Add to .secrets
echo "NEON_API_KEY=your_api_key_here" >> .secrets
```

Get your API key from: https://console.neon.tech/app/settings/api-keys

## GitHub Actions (No Changes Needed!)

The GitHub Actions workflows continue to work exactly as before:

- **PR validation** (`terraform-pr.yml`): Runs on every pull request
- **Production deploy** (`terraform-apply.yml`): Runs on merge to main

Your local development happens in a separate workspace and doesn't affect these workflows.

## Migration from Old Workflow

If you were using the old credential export scripts:

**Old way:**

```bash
source scripts/setup-aws.sh
cd infra
terraform plan
```

**New way:**

```bash
# Edit .secrets once with AWS_PROFILE
cd infra
make local-plan  # That's it!
```

The new workflow is simpler and more reliable:

- No need to source scripts
- No credential exports to environment
- Automatic SSO session management
- Workspace isolation for safety
