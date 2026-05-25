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

output "frontend_s3_website_endpoint" {
  description = "S3 static website endpoint for frontend (should be private if using CloudFront)"
  value       = module.frontend_s3.website_endpoint
}

output "bastion_public_ip" {
  description = "Public IP of bastion host"
  value       = module.bastion.bastion_public_ip
}

output "bastion_ssh_username" {
  description = "SSH username for bastion host"
  value       = module.bastion.bastion_ssh_username
}

output "bastion_ssh_key_name" {
  description = "SSH key name for bastion host"
  value       = module.bastion.bastion_ssh_key_name
}

output "bastion_ssh_port" {
  description = "SSH port for bastion host"
  value       = module.bastion.bastion_ssh_port
}

output "tally_site_url" {
  description = "Full URL for the static site via CloudFront and custom domain."
  value       = "https://${var.project}.${var.domain_name}"
}

output "tally_api_url" {
  description = "Base URL for the API via CloudFront and custom domain."
  value       = "https://${var.project}.${var.domain_name}${var.api_endpoint_prefix}"
}

output "api_gateway_invoke_url" {
  description = "Direct API Gateway invoke URL (for debugging, not for production use)."
  value       = module.api_gateway.invoke_url
}
