variable "lambda_code_s3_bucket" {
  description = "S3 bucket containing the Lambda deployment package (backend.zip)"
  type        = string
}

variable "project" {
  description = "Project"
  type        = string
}


variable "database_url_readwrite" {
  description = "Neon PostgreSQL read-write connection string"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.database_url_readwrite) > 0
    error_message = "database_url_readwrite must not be empty."
  }
}

variable "database_url_readonly" {
  description = "Neon PostgreSQL read-only connection string"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.database_url_readonly) > 0
    error_message = "database_url_readonly must not be empty."
  }
}
