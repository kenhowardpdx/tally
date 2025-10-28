output "rds_instance_id" {
  description = "RDS instance ID"
  value       = aws_db_instance.main.id
}

output "rds_endpoint" {
  description = "RDS endpoint"
  value       = aws_db_instance.main.endpoint
}

output "rds_db_name" {
  description = "RDS database name"
  value       = aws_db_instance.main.name
}

output "rds_username" {
  description = "RDS master username"
  value       = aws_db_instance.main.username
}

output "rds_port" {
  description = "RDS port"
  value       = aws_db_instance.main.port
}

output "rds_password_secret_arn" {
  description = "Secrets Manager ARN for RDS password"
  value       = data.aws_secretsmanager_secret.rds_password.arn
}


