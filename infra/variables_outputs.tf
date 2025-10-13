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

# VPC Module Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "private_subnet_ids" {
  description = "List of IDs of private subnets"
  value       = module.vpc.private_subnets
}

output "public_subnet_ids" {
  description = "List of IDs of public subnets"
  value       = module.vpc.public_subnets
}

output "lambda_security_group_id" {
  description = "ID of the Lambda security group"
  value       = module.vpc.lambda_security_group_id
}

output "rds_security_group_id" {
  description = "ID of the RDS security group"
  value       = module.vpc.rds_security_group_id
}

# Placeholder outputs - commented out until modules are implemented

# output "lambda_function_arn" {
#   value = module.lambda.lambda_function_arn
# }

# output "api_gateway_url" {
#   value = module.api_gateway.invoke_url
# }

# output "acm_certificate_arn" {
#   value = module.acm.certificate_arn
# }

# output "route53_domain_name" {
#   value = module.route53.domain_name
# }
