variable "cloudfront_domain_name" {
  description = "CloudFront distribution domain name for frontend static site."
  type        = string
}

variable "domain_name" {
  description = "The domain name for the Route 53 hosted zone."
  type        = string
}
