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

variable "auth0_domain" {
  description = "Auth0 tenant domain (e.g. your-tenant.us.auth0.com), used for JWKS-based JWT validation"
  type        = string

  validation {
    condition     = length(var.auth0_domain) > 0
    error_message = "auth0_domain must not be empty."
  }
}

variable "auth0_audience" {
  description = "Auth0 API identifier the backend validates JWT audiences against"
  type        = string

  validation {
    condition     = length(var.auth0_audience) > 0
    error_message = "auth0_audience must not be empty."
  }
}
