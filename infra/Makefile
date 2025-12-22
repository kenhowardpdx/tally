# Terraform Infrastructure Makefile
#
# RECOMMENDED LOCAL WORKFLOW:
#   Use ../scripts/tf-local for all local development operations
#   This uses AWS SSO profile authentication and a separate 'local-dev' workspace
#
# Quick Start:
#   make local-init    # Initialize terraform with S3 backend + local-dev workspace
#   make local-plan    # Plan infrastructure changes
#   make local-apply   # Apply changes (prompts for confirmation)
#   make local-destroy # Destroy all local-dev infrastructure (prompts for confirmation)
#
# GitHub Actions Testing:
#   make act-plan      # Test PR workflow with ACT
#   make act-apply     # Test apply workflow with ACT (not recommended)
#
# Direct terraform commands (advanced):
#   All make targets below use the tf-local wrapper for proper authentication
#   You can also run terraform directly if you've sourced .secrets and set up SSO

.PHONY: help local-init local-plan local-apply local-destroy local-fmt local-validate \
        local-workspace local-state act-plan act-apply clean-terraform clean-state \
        aws-credentials init-local

help: ## Show this help message
	@echo "\n🔧 Tally Infrastructure - Local Development\n"
	@echo "Quick Start:"
	@echo "  1. Copy ../.secrets.example to ../.secrets"
	@echo "  2. Set AWS_PROFILE and TF_VAR_aws_account_id in ../.secrets"
	@echo "  3. Run: make local-init"
	@echo "  4. Run: make local-plan\n"
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============================================================================
# Local Development Targets (using scripts/tf-local wrapper)
# ============================================================================

local-init: ## Initialize Terraform with S3 backend and local-dev workspace
	@../scripts/tf-local init

local-plan: ## Run terraform plan for local development
	@../scripts/tf-local plan

local-apply: ## Apply infrastructure changes (local-dev workspace only)
	@../scripts/tf-local apply

local-destroy: ## Destroy all infrastructure in local-dev workspace
	@../scripts/tf-local destroy

local-fmt: ## Format all Terraform files
	@../scripts/tf-local fmt -recursive

local-validate: ## Validate Terraform configuration
	@../scripts/tf-local validate

local-workspace: ## Show current Terraform workspace
	@../scripts/tf-local workspace show

local-state: ## Show Terraform state resources
	@../scripts/tf-local state list

# ============================================================================
# GitHub Actions Testing Targets (using ACT)
# ============================================================================

act-plan: ## Test PR workflow locally with ACT
	@echo "⚠️  Testing GitHub Actions terraform-pr workflow with ACT"
	@echo "Make sure you've run: ../scripts/export-aws-credentials.sh"
	@[ -f "../.secrets" ] || { echo "❌ .secrets file required"; exit 1; }
	@(cd .. && make github_workflow_terraform-pr)

act-apply: ## Test apply workflow locally with ACT (use with caution)
	@echo "⚠️  Testing GitHub Actions terraform-apply workflow with ACT"
	@echo "Make sure you've run: ../scripts/export-aws-credentials.sh"
	@[ -f "../.secrets" ] || { echo "❌ .secrets file required"; exit 1; }
	@(cd .. && make github_workflow_terraform-apply)

# ============================================================================
# Cleanup and Utility Targets
# ============================================================================

clean-terraform: ## Remove Terraform state, lock, and backend files (safe local reset)
	@echo "🧹 Cleaning Terraform local files..."
	@rm -rf .terraform .terraform.lock.hcl backend.tf backend.conf.tmp
	@echo "✓ Cleaned. Run 'make local-init' to reinitialize."

clean-state: ## Remove local terraform state file (WARNING: local backend only)
	@echo "⚠️  This will remove terraform.tfstate - only safe if using S3 backend"
	@read -p "Continue? (yes/no): " confirm && [ "$$confirm" = "yes" ] || exit 1
	@rm -f terraform.tfstate terraform.tfstate.backup
	@echo "✓ Local state files removed"

clean-all: ## Remove all Terraform files including .terraform directory
	@echo "⚠️  This will remove ALL Terraform local files"
	@read -p "Continue? (yes/no): " confirm && [ "$$confirm" = "yes" ] || exit 1
	@rm -rf .terraform .terraform.lock.hcl backend.tf backend.conf.tmp terraform.tfstate terraform.tfstate.backup
	@echo "✓ All Terraform files removed. Run 'make local-init' to start fresh."

# ============================================================================
# Terraform Workspace Management
# ============================================================================

workspace-list: ## List all Terraform workspaces
	@../scripts/tf-local workspace list

workspace-show: ## Show current Terraform workspace
	@../scripts/tf-local workspace show

# ============================================================================
# Terraform State Management
# ============================================================================

state-list: ## List all resources in Terraform state
	@../scripts/tf-local state list

state-show: ## Show details of a specific resource (usage: make state-show RESOURCE=module.vpc.aws_vpc.main)
	@test -n "$(RESOURCE)" || { echo "❌ RESOURCE required. Usage: make state-show RESOURCE=module.vpc.aws_vpc.main"; exit 1; }
	@../scripts/tf-local state show $(RESOURCE)
