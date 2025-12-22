# Neon Terraform Configuration Guide

## Overview

Neon is now configured as a Terraform module, replacing AWS RDS for zero-cost serverless PostgreSQL.

## Setup Steps

### 1. Get Neon API Key

```bash
# Sign up at https://console.neon.tech
# Navigate to Settings → API Keys
# Create a new API key
```

### 2. Set Environment Variable

Add to your `.secrets` file:

```bash
# .secrets
export NEON_API_KEY="your-neon-api-key-here"
export AWS_PROFILE=AdministratorAccess-123456789012
export AWS_ROLE_ARN=arn:aws:iam::123456789012:role/tally-github-actions-role
export TF_VAR_aws_account_id=123456789012
export TF_VAR_aws_profile=AdministratorAccess-123456789012
```

Load the secrets:

```bash
source .secrets
```

### 3. Initialize Terraform

```bash
cd infra
terraform init
terraform plan
```

## Module Configuration

The Neon module is configured in `infra/main.tf`:

```hcl
module "neon" {
  source = "./modules/neon"

  project     = var.project
  environment = var.environment
  region_id   = "aws-us-west-2"  # Match your AWS region

  db_name     = "${var.project}db"
  db_username = "${var.project}admin"
}
```

## Features

### Auto-scaling & Scale-to-Zero

- **Minimum**: 0.25 compute units (CU)
- **Maximum**: 1 CU (free tier limit)
- **Auto-suspend**: After 5 minutes of inactivity
- **Cost**: $0/month within free tier limits

### Free Tier Limits

- **Storage**: 0.5 GB
- **Compute**: Shared compute (auto-scales to zero)
- **Data Transfer**: 10 GB/month
- **Branches**: Unlimited (great for dev/staging)

## Outputs

The module provides these outputs for Lambda integration:

```hcl
module.neon.database_host       # PostgreSQL endpoint
module.neon.database_name       # Database name
module.neon.database_username   # Database user
module.neon.database_password   # Database password (sensitive)
module.neon.connection_uri      # Full connection string
```

## Lambda Integration

Lambda automatically receives database credentials:

```python
# Lambda environment variables (auto-configured)
DB_HOST     = module.neon.database_host
DB_NAME     = module.neon.database_name
DB_USERNAME = module.neon.database_username
DB_PASSWORD = module.neon.database_password
```

## Database Branching

Neon supports database branching (like Git for databases):

```hcl
# Create a dev branch from main
resource "neon_branch" "dev" {
  project_id = module.neon.project_id
  parent_id  = module.neon.branch_id
  name       = "dev"
}
```

## Available Regions

Neon supports these AWS regions:

- `aws-us-east-1` (Virginia)
- `aws-us-east-2` (Ohio)
- `aws-us-west-2` (Oregon)
- `aws-eu-central-1` (Frankfurt)
- `aws-ap-southeast-1` (Singapore)

## Migration from RDS

### 1. Export RDS Data

```bash
# Connect to RDS and export
pg_dump -h <rds-endpoint> -U talleadmin tallydb > backup.sql
```

### 2. Import to Neon

```bash
# Get Neon connection string from Terraform output
terraform output -raw neon_connection_uri

# Import data
psql "$(terraform output -raw neon_connection_uri)" < backup.sql
```

### 3. Update Lambda

Lambda configuration is automatically updated via Terraform outputs.

### 4. Destroy RDS

```bash
terraform destroy -target=module.rds
```

## Cost Comparison

| Database | Monthly Cost | Scales to Zero | Storage |
|----------|--------------|----------------|---------|
| RDS t3.micro | $16.95 | ❌ | 20 GB |
| **Neon (free tier)** | **$0.00** | ✅ | 0.5 GB |
| Neon (paid) | $19.00 | ✅ | 10 GB |

## Monitoring

View database metrics in Neon Console:
- https://console.neon.tech
- Monitor: Compute usage, storage, connections, queries

## Troubleshooting

### API Key Issues

```bash
# Verify API key is set
echo $NEON_API_KEY

# Re-export if needed
source .secrets
```

### Connection Issues

```bash
# Test connection
psql "$(terraform output -raw neon_connection_uri)"

# Check endpoint status in Neon Console
# Endpoints auto-suspend after 5 minutes - first connection may take 1-2 seconds to wake
```

### Terraform Provider Issues

```bash
# Reinitialize providers
cd infra
rm -rf .terraform
terraform init
```

## References

- Neon Docs: https://neon.tech/docs
- Terraform Provider: https://registry.terraform.io/providers/kislerdm/neon
- API Reference: https://api-docs.neon.tech/reference/getting-started-with-neon-api
