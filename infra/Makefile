# IMPORTANT: Always use 'make plan' for AWS authentication.
# NEVER run 'make apply' locally except through testing workflows with ACT.
# This prevents accidental infrastructure changes and unexpected AWS charges.
# For real deployments, use GitHub Actions workflows only.

.PHONY: help aws-login aws-creds act-plan act-apply create-rds-secret init init-local plan show apply validate destroy clean clean-terraform fmt check check-aws setup-aws-credentials workspace-list workspace-new workspace-select state-list state-show dev-setup ci-check

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# AWS Auth
aws-login: ## Authenticate with AWS SSO (for direct terraform use)
	@../scripts/aws-auth.sh

aws-creds: ## Authenticate with AWS SSO and export STS credentials for ACT
	@../scripts/aws-auth.sh --creds

# ACT (GitHub Actions local testing)
# NOTE: For ACT runs, use 'make init-local' to avoid S3 backend issues.
act-plan: ## Run GitHub Actions workflow (terraform-pr) with AWS creds
	@[ -f "../.secrets" ] || { echo "❌ .secrets file required. Run 'make aws-creds' first."; exit 1; }
	@[ -f "$$HOME/.aws/credentials" ] || { echo "❌ ~/.aws/credentials not found. Run 'make aws-creds' first."; exit 1; }
	set -a && source ../.secrets && set +a && \
	(cd .. && act -j validate \
		--secret-file .secrets \
		--env AWS_PROFILE=$$AWS_PROFILE \
		--env AWS_ROLE_ARN=$$AWS_ROLE_ARN \
		--env TF_VAR_aws_account_id=$$TF_VAR_aws_account_id \
		--env TF_VAR_aws_profile=$$TF_VAR_aws_profile \
		-v $$HOME/.aws:/root/.aws)

act-apply: ## Run GitHub Actions workflow (terraform-apply) with AWS creds
	@[ -f "../.secrets" ] || { echo "❌ .secrets file required. Run 'make aws-creds' first."; exit 1; }
	@[ -f "$$HOME/.aws/credentials" ] || { echo "❌ ~/.aws/credentials not found. Run 'make aws-creds' first."; exit 1; }
	set -a && source ../.secrets && set +a && \
	(cd .. && act -j apply \
		--secret-file .secrets \
		--env AWS_PROFILE=$$AWS_PROFILE \
		--env AWS_ROLE_ARN=$$AWS_ROLE_ARN \
		--env TF_VAR_aws_account_id=$$TF_VAR_aws_account_id \
		--env TF_VAR_aws_profile=$$TF_VAR_aws_profile \
		-v $$HOME/.aws:/root/.aws)

# Secrets
create-rds-secret: ## Create RDS password secret in Secrets Manager (no-op if it already exists)
	@if aws secretsmanager describe-secret --secret-id prod-rds-postgres-password >/dev/null 2>&1; then \
		echo "✅ Secret 'prod-rds-postgres-password' already exists, skipping."; \
	else \
		password=$$(openssl rand -base64 32 | tr -d '/+='); \
		arn=$$(aws secretsmanager create-secret \
			--name prod-rds-postgres-password \
			--description "RDS PostgreSQL password for Tally prod" \
			--secret-string "$$password" \
			--query ARN --output text) && \
		echo "✅ Secret created: $$arn"; \
	fi

# Terraform
init: ## Initialize Terraform with S3 backend (CI/remote only)
	@[ -f "../.secrets" ] || { echo "❌ .secrets file required"; exit 1; }
	@set -a && source ../.secrets && set +a && \
	 sed "s/__AWS_ACCOUNT_ID__/$$TF_VAR_aws_account_id/g" backend.conf > backend.conf.tmp && \
	 terraform init -backend-config=backend.conf.tmp

init-local: ## Initialize Terraform with local backend (for ACT/local runs)
	@$(MAKE) clean-terraform
	@echo "Initializing Terraform with local backend..."
	terraform init -reconfigure

plan: ## Run terraform plan
	@[ -f "../.secrets" ] && set -a && source ../.secrets && set +a || true; \
	 terraform plan

show: ## Show current terraform state
	@[ -f "../.secrets" ] && set -a && source ../.secrets && set +a || true; \
	 terraform show

apply: ## Run terraform apply (CI/GitHub Actions only)
	@if [ -z "$$GITHUB_ACTIONS" ] && [ -z "$$MANUAL_TF_APPLY" ]; then \
		echo "❌ Refusing to run apply: Only allowed in GitHub Actions CI or with MANUAL_TF_APPLY=1"; \
		exit 1; \
	fi
	@[ -f "../.secrets" ] && set -a && source ../.secrets && set +a || true; \
	 terraform apply

validate: ## Validate Terraform configuration
	@terraform validate

destroy: ## Destroy all managed infrastructure
	@read -p "⚠️  DESTROY all resources? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@[ -f "../.secrets" ] && set -a && source ../.secrets && set +a || true; \
	 terraform destroy

fmt: ## Format Terraform files
	@terraform fmt -recursive

clean: ## Clean Terraform cache (prompts for confirmation)
	@read -p "Remove .terraform cache? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@rm -rf .terraform .terraform.lock.hcl

clean-terraform: ## Remove all Terraform state, lock, and backend config files (safe local reset)
	@echo "Removing .terraform, .terraform.lock.hcl, backend.conf.tmp..."
	rm -rf .terraform .terraform.lock.hcl backend.conf.tmp ../.github/workflows/backend.conf.json

check: ## Check if Terraform is installed
	@which terraform > /dev/null || { echo "❌ Terraform not found"; exit 1; }

check-aws: check ## Check if AWS credentials are configured
	@aws sts get-caller-identity >/dev/null 2>&1 || $(MAKE) -s setup-aws-credentials

setup-aws-credentials: ## Internal: authenticate with AWS SSO
	@../scripts/aws-auth.sh

workspace-list: ## List Terraform workspaces
	@terraform workspace list

workspace-new: ## Create a new Terraform workspace (NAME=<name>)
	@test -n "$(NAME)" || { echo "❌ NAME required"; exit 1; }
	@terraform workspace new $(NAME)

workspace-select: ## Select a Terraform workspace (NAME=<name>)
	@test -n "$(NAME)" || { echo "❌ NAME required"; exit 1; }
	@terraform workspace select $(NAME)

state-list: ## List resources in Terraform state
	@terraform state list

state-show: ## Show a resource in Terraform state (RESOURCE=<resource>)
	@test -n "$(RESOURCE)" || { echo "❌ RESOURCE required"; exit 1; }
	@terraform state show $(RESOURCE)

dev-setup: check aws-login init validate ## Complete development setup

ci-check: check validate fmt ## CI/CD validation checks
	@terraform fmt -check -recursive || { echo "❌ Run 'make fmt'"; exit 1; }
