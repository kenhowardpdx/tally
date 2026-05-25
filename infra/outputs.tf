output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name for frontend static site"
  value       = module.cloudfront.cloudfront_domain_name
}

output "frontend_s3_website_endpoint" {
  description = "S3 static website endpoint for frontend (should be private if using CloudFront)"
  value       = module.frontend_s3.website_endpoint
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
