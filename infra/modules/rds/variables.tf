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

variable "backup_retention_period" {
  description = "Number of days to retain automated backups. Set to 0 to disable (zero cost). Increase to 7-35 when ready for production backups."
  type        = number
  default     = 0
}
