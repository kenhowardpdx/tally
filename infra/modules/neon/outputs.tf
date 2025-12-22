output "project_id" {
  description = "Neon project ID"
  value       = data.neon_project.shared.id
}

output "database_host" {
  description = "Database host endpoint"
  value       = neon_endpoint.this.host
}

output "database_name" {
  description = "Database name"
  value       = neon_database.this.name
}

output "database_username" {
  description = "Database username"
  value       = neon_role.this.name
}

output "database_password" {
  description = "Database password (sensitive)"
  value       = neon_role.this.password
  sensitive   = true
}

output "connection_uri" {
  description = "Full PostgreSQL connection URI (sensitive)"
  value       = "postgresql://${neon_role.this.name}:${neon_role.this.password}@${neon_endpoint.this.host}/${neon_database.this.name}?sslmode=require"
  sensitive   = true
}

output "endpoint_id" {
  description = "Neon endpoint ID"
  value       = neon_endpoint.this.id
}

output "branch_id" {
  description = "Neon branch ID for this environment"
  value       = neon_branch.env.id
}
