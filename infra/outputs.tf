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
  value       = module.route53.domain_name
}

output "route53_name_servers" {
  description = "Route 53 hosted zone name servers (for registrar setup)"
  value       = module.route53.name_servers
}

output "frontend_s3_website_endpoint" {
  description = "S3 static website endpoint for frontend (should be private if using CloudFront)"
  value       = module.frontend_s3.website_endpoint
}
output "db_instance_id" {
  description = "RDS instance ID"
  value       = module.rds.rds_instance_id
}

output "db_endpoint" {
  description = "RDS endpoint"
  value       = module.rds.rds_endpoint
}

output "db_name" {
  description = "RDS database name"
  value       = module.rds.rds_db_name
}

output "db_username" {
  description = "RDS database username"
  value       = module.rds.rds_username
}

output "db_port" {
  description = "RDS port"
  value       = module.rds.rds_port
}

output "db_password_secret_arn" {
  description = "Secrets Manager ARN for RDS password"
  value       = data.aws_secretsmanager_secret.rds_password.arn
}

output "db_connection_string" {
  description = "PostgreSQL connection string (password in Secrets Manager)"
  value       = "postgresql://${module.rds.rds_username}:[password-from-secrets]@${module.rds.rds_endpoint}:${module.rds.rds_port}/${module.rds.rds_db_name}"
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
