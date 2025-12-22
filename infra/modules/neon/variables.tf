variable "environment" {
  description = "Environment name (dev, staging, prod) - dev uses default branch, others create new branches"
  type        = string
}

variable "neon_project_id" {
  description = "Shared Neon project ID (super-water-91030697)"
  type        = string
}

variable "db_name" {
  description = "Database name"
  type        = string
}

variable "db_username" {
  description = "Database username"
  type        = string
}
