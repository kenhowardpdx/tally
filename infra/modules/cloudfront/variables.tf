variable "bucket_name" {
  description = "Name of the S3 bucket to serve via CloudFront."
  type        = string
}

variable "aliases" {
  description = "Alternate domain names (CNAMEs) for the CloudFront distribution."
  type        = list(string)
  default     = []
}

variable "acm_certificate_arn" {
  description = "ARN of the ACM certificate for SSL."
  type        = string
  default     = null
}

variable "api_gateway_domain_name" {
  description = "Domain name of the API Gateway stage invoke URL (e.g., xxxxx.execute-api.us-west-2.amazonaws.com)."
  type        = string
  default     = null
}

variable "api_path_pattern" {
  description = "Path pattern for API requests."
  type        = string
  default     = "/api/v1/*"
}

variable "tags" {
  description = "Tags to apply to CloudFront resources."
  type        = map(string)
}
