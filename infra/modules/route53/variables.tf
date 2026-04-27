variable "cloudfront_domain_name" {
  description = "CloudFront distribution domain name for frontend static site."
  type        = string
}

variable "cloudfront_hosted_zone_id" {
  description = "CloudFront distribution hosted zone ID for Route 53 alias records."
  type        = string
}

variable "domain_name" {
  description = "The domain name for the Route 53 hosted zone."
  type        = string
}
