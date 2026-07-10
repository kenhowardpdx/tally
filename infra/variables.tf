variable "api_endpoint_prefix" {
  description = "API endpoint prefix for routing (e.g., /api/v1/)"
  type        = string
  default     = "/api/v1/"
}

variable "domain_name" {
  description = "Base domain name for the project (e.g., kenhoward.dev)"
  type        = string
  default     = "kenhoward.dev"
}

variable "project" {
  description = "Project name"
  type        = string
  default     = "tally"
}

variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-west-2"
}

variable "aws_account_id" {
  description = "AWS Account ID for S3 state bucket and profile configuration"
  type        = string
  # Local dev: Set via environment variable TF_VAR_aws_account_id (from .secrets)
  # GitHub Actions: Set via repository secrets
}

variable "aws_profile" {
  description = "AWS CLI profile to use for authentication (local development only)"
  type        = string
  default     = null
  # Local dev: Set via environment variable TF_VAR_aws_profile (from .secrets)
  # GitHub Actions: Uses OIDC, so this is ignored
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
  # Set via environment variable TF_VAR_environment
  # GitHub Actions: Uses workflow inputs or defaults to production

  validation {
    # Only "prod" is supported today: infra/backend.conf hardcodes a single shared
    # state key, and the CloudFront alias/ACM cert (infra/main.tf's frontend_domain)
    # aren't environment-parameterized. A non-prod apply would reuse prod's state,
    # force-replace the (immutable) API Gateway stage, and repoint the live prod
    # CloudFront distribution instead of creating an isolated environment. Expand
    # this list only after those pieces are also made environment-aware.
    condition     = var.environment == "prod"
    error_message = "environment must be \"prod\" - see the validation block comment for why other values aren't safe yet."
  }
}

variable "database_url_readwrite" {
  description = "Neon PostgreSQL read-write connection string for the backend Lambda"
  type        = string
  sensitive   = true
  # Set via TF_VAR_database_url_readwrite or GitHub Actions secret TALLY_DATABASE_URL_READWRITE

  validation {
    condition     = length(var.database_url_readwrite) > 0
    error_message = "database_url_readwrite must not be empty."
  }
}

variable "database_url_readonly" {
  description = "Neon PostgreSQL read-only connection string for the backend Lambda"
  type        = string
  sensitive   = true
  # Set via TF_VAR_database_url_readonly or GitHub Actions secret TALLY_DATABASE_URL_READONLY

  validation {
    condition     = length(var.database_url_readonly) > 0
    error_message = "database_url_readonly must not be empty."
  }
}
