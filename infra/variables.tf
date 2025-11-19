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
}
