output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "List of IDs of public subnets (for Lambda functions)"
  value       = module.vpc.public_subnet_ids
}

output "lambda_security_group_id" {
  description = "ID of the Lambda security group"
  value       = module.vpc.lambda_security_group_id
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name for frontend static site"
  value       = module.cloudfront.cloudfront_domain_name
}

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

output "route53_domain_name" {
  description = "Route 53 hosted zone domain name"
  value       = var.environment == "prod" ? module.route53[0].domain_name : null
}

output "route53_name_servers" {
  description = "Route 53 hosted zone name servers (for registrar setup)"
  value       = var.environment == "prod" ? module.route53[0].name_servers : null
}

output "frontend_s3_website_endpoint" {
  description = "S3 static website endpoint for frontend (should be private if using CloudFront)"
  value       = module.frontend_s3.website_endpoint
}

# Neon Database Outputs
output "neon_project_id" {
  description = "Neon project ID"
  value       = module.neon.project_id
}

output "neon_database_host" {
  description = "Neon database host endpoint"
  value       = module.neon.database_host
  sensitive   = true
}

output "neon_database_name" {
  description = "Neon database name"
  value       = module.neon.database_name
}

output "neon_connection_uri" {
  description = "Neon PostgreSQL connection URI"
  value       = module.neon.connection_uri
  sensitive   = true
}

output "tally_site_url" {
  description = "Full URL for the static site"
  value       = var.environment == "prod" ? "https://${var.project}.${var.domain_name}" : "https://${module.cloudfront.cloudfront_domain_name}"
}

output "tally_api_url" {
  description = "Base URL for the API"
  value       = var.environment == "prod" ? "https://${var.project}.${var.domain_name}${var.api_endpoint_prefix}" : "https://${module.cloudfront.cloudfront_domain_name}${var.api_endpoint_prefix}"
}

output "api_gateway_invoke_url" {
  description = "Direct API Gateway invoke URL (for debugging)"
  value       = module.api_gateway.invoke_url
}

# Environment-specific access instructions
output "access_instructions" {
  description = "How to access your deployed application"
  value = var.environment == "prod" ? "Production: Access via https://tally.kenhoward.dev" : <<-EOT
    Development Environment
    =======================
    Frontend: https://${module.cloudfront.cloudfront_domain_name}
    API:      https://${module.cloudfront.cloudfront_domain_name}${var.api_endpoint_prefix}
    
    Note: Using auto-generated CloudFront domain (no custom domain in dev)
  EOT
}
