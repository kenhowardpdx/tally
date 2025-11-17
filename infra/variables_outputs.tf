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

# VPC Module Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "List of IDs of public subnets (for Lambda functions)"
  value       = module.vpc.public_subnet_ids
}

output "database_subnet_ids" {
  description = "List of IDs of database subnets (for RDS subnet group)"
  value       = module.vpc.database_subnet_ids
}

output "lambda_security_group_id" {
  description = "ID of the Lambda security group"
  value       = module.vpc.lambda_security_group_id
}

output "rds_security_group_id" {
  description = "ID of the RDS security group"
  value       = module.vpc.rds_security_group_id
}

output "rds_password_secret_arn" {
  description = "Secrets Manager ARN for RDS password"
  value       = data.aws_secretsmanager_secret.rds_password.arn
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

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name for frontend static site"
  value       = module.cloudfront.cloudfront_domain_name
}

# VPC Module Additional Outputs
output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = module.vpc.vpc_cidr_block
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = module.vpc.internet_gateway_id
}

output "public_route_table_id" {
  description = "ID of the public route table"
  value       = module.vpc.public_route_table_id
}


# Route 53 outputs for DNS setup
output "route53_domain_name" {
  description = "Route 53 hosted zone domain name"
  value       = module.route53.domain_name
}

output "route53_name_servers" {
  description = "Route 53 hosted zone name servers (for registrar setup)"
  value       = module.route53.name_servers
}

# S3 website endpoint output for reference
output "frontend_s3_website_endpoint" {
  description = "S3 static website endpoint for frontend (should be private if using CloudFront)"
  value       = module.frontend_s3.website_endpoint
}
