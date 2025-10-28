variable "bucket_name" {
  description = "Name of the S3 bucket to serve via CloudFront."
  type        = string
}

variable "tags" {
  description = "Tags to apply to CloudFront resources."
  type        = map(string)
}
