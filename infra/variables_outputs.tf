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

# Outputs for modules - commented out until modules are implemented

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
