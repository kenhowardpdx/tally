
variable "cloudfront_distribution_arn" {
  description = "CloudFront distribution ARN for bucket policy"
  type        = string
}
variable "bucket_name" {
  description = "Name of the S3 bucket for frontend static site."
  type        = string
}

variable "tags" {
  description = "Tags to apply to the S3 bucket."
  type        = map(string)
}

variable "aws_account_id" {
  description = "AWS Account ID for CloudFront policy."
  type        = string
}
