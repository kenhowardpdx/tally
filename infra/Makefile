# IMPORTANT: Always use 'make plan' for AWS authentication.
# NEVER run 'make apply' locally except through testing workflows with ACT.
# This prevents accidental infrastructure changes and unexpected AWS charges.
# For real deployments, use GitHub Actions workflows only.
# Do NOT run 'terraform apply' or 'make apply' directly unless you are in a safe test environment.

# Terraform Infrastructure Makefile

.PHONY: act-plan act-apply
# Run ACT with AWS credentials from .secrets








act-plan: ## Run GitHub Actions workflow (terraform-pr) with AWS creds (from project root, mounts ~/.aws)
	@[ -f "../.secrets" ] || { echo "❌ .secrets file required"; exit 1; }
	[ -f "$$HOME/.aws/credentials" ] || { echo "❌ ~/.aws/credentials not found or not mounted. ACT will fail. See docs for setup."; exit 1; }
	set -a && source ../.secrets && set +a && \
	ACT_ENV="AWS_PROFILE=$$AWS_PROFILE AWS_ROLE_ARN=$$AWS_ROLE_ARN TF_VAR_aws_account_id=$$TF_VAR_aws_account_id TF_VAR_aws_profile=$$TF_VAR_aws_profile" && \
	echo "Running: (cd .. && act -j validate --env AWS_PROFILE=$$AWS_PROFILE --env AWS_ROLE_ARN=$$AWS_ROLE_ARN --env TF_VAR_aws_account_id=$$TF_VAR_aws_account_id --env TF_VAR_aws_profile=$$TF_VAR_aws_profile -v $$HOME/.aws:/root/.aws)" && \
	(cd .. && act -j validate --env AWS_PROFILE=$$AWS_PROFILE --env AWS_ROLE_ARN=$$AWS_ROLE_ARN --env TF_VAR_aws_account_id=$$TF_VAR_aws_account_id --env TF_VAR_aws_profile=$$TF_VAR_aws_profile -v $$HOME/.aws:/root/.aws)









act-apply: ## Run GitHub Actions workflow (terraform-apply) with AWS creds (from project root, mounts ~/.aws)
	@[ -f "../.secrets" ] || { echo "❌ .secrets file required"; exit 1; }
	[ -f "$$HOME/.aws/credentials" ] || { echo "❌ ~/.aws/credentials not found or not mounted. ACT will fail. See docs for setup."; exit 1; }
	set -a && source ../.secrets && set +a && \
	ACT_ENV="AWS_PROFILE=$$AWS_PROFILE AWS_ROLE_ARN=$$AWS_ROLE_ARN TF_VAR_aws_account_id=$$TF_VAR_aws_account_id TF_VAR_aws_profile=$$TF_VAR_aws_profile" && \
	echo "Running: (cd .. && act -j apply --env AWS_PROFILE=$$AWS_PROFILE --env AWS_ROLE_ARN=$$AWS_ROLE_ARN --env TF_VAR_aws_account_id=$$TF_VAR_aws_account_id --env TF_VAR_aws_profile=$$TF_VAR_aws_profile -v $$HOME/.aws:/root/.aws)" && \
	(cd .. && act -j apply --env AWS_PROFILE=$$AWS_PROFILE --env AWS_ROLE_ARN=$$AWS_ROLE_ARN --env TF_VAR_aws_account_id=$$TF_VAR_aws_account_id --env TF_VAR_aws_profile=$$TF_VAR_aws_profile -v $$HOME/.aws:/root/.aws)
#
# NOTE: For local development and ACT runs, use 'make init-local' to avoid S3 backend issues.
# 'make init' is ONLY for remote/CI use and will configure the S3 backend.

.PHONY: help aws-setup aws-credentials init init-local plan show apply validate destroy clean fmt check clean-terraform
# Export AWS SSO credentials to ~/.aws/credentials in INI format
aws-credentials: ## Export AWS SSO credentials to ~/.aws/credentials in INI format
	@../scripts/export-aws-credentials.sh
clean-terraform: ## Remove all Terraform state, lock, and backend config files (safe local reset)
	@echo "Removing .terraform, .terraform.lock.hcl, backend.conf, backend.conf.json..."
	rm -rf .terraform .terraform.lock.hcl backend.conf ../.github/workflows/backend.conf.json

init-local: ## Initialize Terraform with local backend (for ACT/local runs)
	@$(MAKE) clean-terraform
	@echo "Initializing Terraform with local backend..."
	terraform init -reconfigure


help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

aws-setup: ## Configure AWS SSO credentials
	@../scripts/aws-setup.sh

	@[ -f "../.secrets" ] || { echo "❌ .secrets file required"; exit 1; }
	@set -a && source ../.secrets && set +a && \
	 printf "bucket=\"terraform-state-$$TF_VAR_aws_account_id\"\nkey=\"tally/prod/terraform.tfstate\"\nregion=\"us-west-2\"\nencrypt=true\n" > backend.conf && \
	 terraform init -backend-config=backend.conf

	@[ -f "../.secrets" ] && set -a && source ../.secrets && set +a || true; \
	 terraform plan

	@[ -f "../.secrets" ] && set -a && source ../.secrets && set +a || true; \
	 terraform show

	if [ -z "$$GITHUB_ACTIONS" ] && [ -z "$$MANUAL_TF_APPLY" ]; then \
		echo "❌ Refusing to run apply: Only allowed in GitHub Actions CI or with MANUAL_TF_APPLY=1"; \
		exit 1; \
	fi
	@[ -f "../.secrets" ] && set -a && source ../.secrets && set +a || true; \
	 terraform apply

validate: ## Validate Terraform configuration
	@terraform validate

	@read -p "⚠️  DESTROY all resources? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@[ -f "../.secrets" ] && set -a && source ../.secrets && set +a || true; \
	 terraform destroy

fmt: ## Format Terraform files
	@terraform fmt -recursive

clean: ## Clean Terraform cache and state files
	@read -p "Remove .terraform cache? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@rm -rf .terraform .terraform.lock.hcl

	@echo "No cached credentials to clean."

check: ## Check if Terraform is installed
	@which terraform > /dev/null || { echo "❌ Terraform not found"; exit 1; }

check-aws: check ## Check if AWS credentials are configured
	@$(MAKE) -s check-aws-smart

	aws sts get-caller-identity >/dev/null 2>&1 || $(MAKE) -s setup-aws-credentials

setup-aws-credentials: ## Internal: Set up AWS SSO credentials (delegated to script)
	@../scripts/aws-setup.sh

	@terraform workspace list

	@test -n "$(NAME)" || { echo "❌ NAME required"; exit 1; }
	@terraform workspace new $(NAME)

	@test -n "$(NAME)" || { echo "❌ NAME required"; exit 1; }
	@terraform workspace select $(NAME)

	@terraform state list

	@test -n "$(RESOURCE)" || { echo "❌ RESOURCE required"; exit 1; }
	@terraform state show $(RESOURCE)

dev-setup: check aws-setup init validate ## Complete development setup

ci-check: check validate fmt ## CI/CD validation checks
	@terraform fmt -check -recursive || { echo "❌ Run 'make fmt'"; exit 1; }
