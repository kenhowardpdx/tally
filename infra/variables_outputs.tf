variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-west-2"
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
