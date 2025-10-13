# Terraform Infrastructure Makefile

.PHONY: help aws-setup init plan show apply validate destroy clean fmt check

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

aws-setup: ## Configure AWS SSO credentials
	@$(MAKE) -s check-aws-smart

init: aws-setup ## Initialize Terraform with remote backend
	@[ -f "../.secrets" ] || { echo "❌ .secrets file required"; exit 1; }
	@set -a && source ../.secrets && set +a && \
	 printf "bucket=\"terraform-state-$$TF_VAR_aws_account_id\"\nkey=\"tally/prod/terraform.tfstate\"\nregion=\"us-west-2\"\nencrypt=true\n" > backend.conf && \
	 source .aws-credentials && terraform init -backend-config=backend.conf

plan: aws-setup ## Create and show Terraform execution plan
	@([ -f "../.secrets" ] && set -a && source ../.secrets && set +a) || true; \
	 source .aws-credentials && terraform plan

show: aws-setup ## Show current Terraform state
	@[ -f "../.secrets" ] && set -a && source ../.secrets && set +a; \
	 source .aws-credentials && terraform show

apply: aws-setup ## Apply Terraform configuration
	@read -p "Apply changes? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@[ -f "../.secrets" ] && set -a && source ../.secrets && set +a; \
	 source .aws-credentials && terraform apply

validate: ## Validate Terraform configuration
	@terraform validate

destroy: aws-setup ## Destroy Terraform-managed infrastructure
	@read -p "⚠️  DESTROY all resources? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@[ -f "../.secrets" ] && set -a && source ../.secrets && set +a; \
	 source .aws-credentials && terraform destroy

fmt: ## Format Terraform files
	@terraform fmt -recursive

clean: ## Clean Terraform cache and state files
	@read -p "Remove .terraform cache? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@rm -rf .terraform .terraform.lock.hcl

clean-credentials: ## Remove cached AWS credentials
	@rm -f .aws-credentials

check: ## Check if Terraform is installed
	@which terraform > /dev/null || { echo "❌ Terraform not found"; exit 1; }

check-aws: check ## Check if AWS credentials are configured
	@$(MAKE) -s check-aws-smart

check-aws-smart: check ## Smart AWS credential checking with auto-setup
	@[ -f ".aws-credentials" ] && source .aws-credentials; \
	 aws sts get-caller-identity >/dev/null 2>&1 || $(MAKE) -s setup-aws-credentials

setup-aws-credentials: ## Internal: Set up and cache AWS credentials
	@[ -f "../.secrets" ] && set -a && source ../.secrets && set +a; \
	 [ -n "$$AWS_PROFILE" ] || { echo "❌ AWS_PROFILE required. Add to ../.secrets or export"; exit 1; }; \
	 aws sso login --profile "$$AWS_PROFILE" && \
	 aws configure export-credentials --profile "$$AWS_PROFILE" --format env > .aws-credentials && \
	 echo "# Cached at $$(date)" >> .aws-credentials

workspace-list: aws-setup ## List Terraform workspaces
	@source .aws-credentials && terraform workspace list

workspace-new: aws-setup ## Create new Terraform workspace (usage: make workspace-new NAME=myworkspace)
	@test -n "$(NAME)" || { echo "❌ NAME required"; exit 1; }
	@source .aws-credentials && terraform workspace new $(NAME)

workspace-select: aws-setup ## Select Terraform workspace (usage: make workspace-select NAME=myworkspace)
	@test -n "$(NAME)" || { echo "❌ NAME required"; exit 1; }
	@source .aws-credentials && terraform workspace select $(NAME)

state-list: aws-setup ## List resources in Terraform state
	@source .aws-credentials && terraform state list

state-show: aws-setup ## Show specific resource from state (usage: make state-show RESOURCE=aws_instance.example)
	@test -n "$(RESOURCE)" || { echo "❌ RESOURCE required"; exit 1; }
	@source .aws-credentials && terraform state show $(RESOURCE)

dev-setup: check aws-setup init validate ## Complete development setup

ci-check: check validate fmt ## CI/CD validation checks
	@terraform fmt -check -recursive || { echo "❌ Run 'make fmt'"; exit 1; }
