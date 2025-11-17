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

variable "db_name" {
  description = "Database name for backend connection"
  type        = string
}

variable "db_username" {
  description = "Database username for backend connection"
  type        = string
}

variable "db_password" {
  description = "Database password for backend connection"
  type        = string
}

variable "db_host" {
  description = "Database host for backend connection"
  type        = string
}
