variable "lambda_code_s3_bucket" {
  description = "S3 bucket containing the Lambda deployment package (backend.zip)"
  type        = string
}

variable "project" {
  description = "Project"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID for Lambda networking"
  type        = string
}

variable "public_subnet_ids" {
  description = "List of public subnet IDs for Lambda networking"
  type        = list(string)
}

variable "lambda_security_group_id" {
  description = "Security group ID for Lambda"
  type        = string
}

variable "database_url_readwrite" {
  description = "Neon PostgreSQL read-write connection string"
  type        = string
  default     = ""
}

variable "database_url_readonly" {
  description = "Neon PostgreSQL read-only connection string"
  type        = string
  default     = ""
}
