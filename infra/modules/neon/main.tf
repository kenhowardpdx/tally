# Neon Serverless PostgreSQL Module
# Provides truly serverless PostgreSQL with scale-to-zero capability
# Free tier: 0.5 GB storage, 10 GB data transfer/month
#
# Architecture: One manually-managed project with Terraform-managed branches
# Project (super-water-91030697) is managed outside Terraform for safety
# Terraform only manages environment branches (development, production)

terraform {
  required_providers {
    neon = {
      source  = "kislerdm/neon"
      version = "~> 0.6"
    }
  }
}

# Reference existing Neon project (managed outside Terraform)
# Project: example-project-12345678 (tally)
# Created manually at: https://console.neon.tech
data "neon_project" "shared" {
  id = var.neon_project_id
}

locals {
  # Map short environment names to full branch names
  branch_name_map = {
    dev  = "development"
    prod = "production"
  }
  branch_name = lookup(local.branch_name_map, var.environment, var.environment)
}

# Create environment-specific database branch
# Each environment (dev, prod, staging, etc.) gets its own named branch
resource "neon_branch" "env" {
  project_id = data.neon_project.shared.id
  name       = local.branch_name
}

# Create database endpoint for this branch
resource "neon_endpoint" "this" {
  project_id = data.neon_project.shared.id
  branch_id  = neon_branch.env.id
  type       = "read_write"

  autoscaling_limit_min_cu = 0.25
  autoscaling_limit_max_cu = 1
}

# Create database on this branch
resource "neon_database" "this" {
  project_id = data.neon_project.shared.id
  branch_id  = neon_branch.env.id
  name       = var.db_name
  owner_name = neon_role.this.name
}

# Create database role (user) for this branch
resource "neon_role" "this" {
  project_id = data.neon_project.shared.id
  branch_id  = neon_branch.env.id
  name       = var.db_username

  depends_on = [neon_endpoint.this]
}
