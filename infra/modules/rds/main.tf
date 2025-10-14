# RDS PostgreSQL Module - Cost-Optimized for Free Tier

resource "aws_db_instance" "main" {
  allocated_storage       = 20 # Free tier limit
  engine                  = "postgres"
  engine_version          = "15.14"       # Supported version for us-west-2
  instance_class          = "db.t3.micro" # Free tier eligible
  db_name                 = var.db_name
  username                = var.db_username
  password                = var.db_password # Should be stored in Secrets Manager
  db_subnet_group_name    = var.db_subnet_group
  vpc_security_group_ids  = var.security_group_ids
  skip_final_snapshot     = true
  publicly_accessible     = false
  multi_az                = false # Single AZ for lowest cost
  backup_retention_period = 0     # No backups for zero cost
  deletion_protection     = false
  tags                    = var.tags
}

# Secrets Manager integration (password rotation, etc.)

# Secret is now managed manually in AWS Secrets Manager.
# Name: ${var.environment}-rds-postgres-password
# Description: RDS PostgreSQL password for ${var.environment}
# Tags: ${var.tags}
# Recovery window: 7 days
# Rotation: (keep as previously configured)

