variable "db_name" {
  description = "Database name"
  type        = string
}

variable "db_username" {
  description = "Master username"
  type        = string
}

variable "db_password" {
  description = "Master password (should come from Secrets Manager)"
  type        = string
  sensitive   = true
}

variable "db_subnet_group" {
  description = "DB subnet group name"
  type        = string
}

variable "security_group_ids" {
  description = "List of security group IDs for RDS"
  type        = list(string)
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
}

variable "environment" {
  description = "Environment name"
  type        = string
}
