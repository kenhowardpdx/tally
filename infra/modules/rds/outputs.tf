output "rds_instance_id" {
  description = "RDS instance ID"
  value       = aws_db_instance.main.id
}

output "rds_endpoint" {
  description = "RDS endpoint"
  value       = aws_db_instance.main.endpoint
}

output "rds_secret_arn" {
  description = "Secrets Manager ARN for DB password"
  value       = aws_secretsmanager_secret.db.arn
}
