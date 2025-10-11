# Terraform Infrastructure Makefile
# This Makefile provides convenient commands for managing Terraform infrastructure
# with AWS SSO authentication via the setup-aws.sh script

.PHONY: help aws-setup init plan show apply validate destroy clean fmt check

# Default target
help: ## Show this help message
	@echo "Terraform Infrastructure Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Typical workflow:"
	@echo "  1. make aws-setup    # Configure AWS SSO credentials"
	@echo "  2. make init         # Initialize Terraform"
	@echo "  3. make plan         # Review planned changes"
	@echo "  4. make apply        # Apply changes"

# AWS Setup - intelligent credential management
aws-setup: ## Configure AWS SSO credentials with caching and expiration handling
	@echo "🔍 Checking AWS credentials..."
	@$(MAKE) -s check-aws-smart

# Terraform Commands with .secrets support
init: aws-setup ## Initialize Terraform with remote backend
	@echo "🚀 Initializing Terraform..."
	@if [ -f "../.secrets" ]; then \
		echo "📁 Loading configuration from .secrets..."; \
		set -a && source ../.secrets && set +a; \
		echo "bucket=\"terraform-state-$$TF_VAR_aws_account_id\"" > backend.conf; \
		echo "key=\"tally/prod/terraform.tfstate\"" >> backend.conf; \
		echo "region=\"us-west-2\"" >> backend.conf; \
		echo "encrypt=true" >> backend.conf; \
		source .aws-credentials && terraform init -backend-config=backend.conf; \
	else \
		echo "❌ .secrets file not found. Please create it with TF_VAR_aws_account_id"; \
		exit 1; \
	fi

plan: aws-setup ## Create and show Terraform execution plan
	@echo "📋 Creating Terraform plan..."
	@if [ -f "../.secrets" ]; then set -a && source ../.secrets && set +a; fi && \
	 source .aws-credentials && terraform plan

show: aws-setup ## Show current Terraform state
	@echo "👀 Showing Terraform state..."
	@if [ -f "../.secrets" ]; then set -a && source ../.secrets && set +a; fi && \
	 source .aws-credentials && terraform show

apply: aws-setup ## Apply Terraform configuration
	@echo "⚡ Applying Terraform configuration..."
	@echo "⚠️  This will make changes to your AWS infrastructure!"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@if [ -f "../.secrets" ]; then set -a && source ../.secrets && set +a; fi && \
	 source .aws-credentials && terraform apply

validate: ## Validate Terraform configuration
	@echo "✅ Validating Terraform configuration..."
	terraform validate

destroy: aws-setup ## Destroy Terraform-managed infrastructure
	@echo "💥 Destroying Terraform infrastructure..."
	@echo "⚠️  This will DELETE all resources managed by Terraform!"
	@read -p "Are you sure you want to destroy everything? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@if [ -f "../.secrets" ]; then set -a && source ../.secrets && set +a; fi && \
	 source .aws-credentials && terraform destroy

# Utility Commands
fmt: ## Format Terraform files
	@echo "📝 Formatting Terraform files..."
	terraform fmt -recursive

clean: ## Clean Terraform cache and state files (use with caution)
	@echo "🧹 Cleaning Terraform cache..."
	@read -p "This will remove .terraform directory and .terraform.lock.hcl. Continue? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	rm -rf .terraform
	rm -f .terraform.lock.hcl

clean-credentials: ## Remove cached AWS credentials (forces re-authentication)
	@echo "🗑️  Removing cached AWS credentials..."
	@rm -f .aws-credentials
	@echo "✅ Cached credentials removed. Next command will trigger re-authentication."

check: ## Check if Terraform is installed
	@echo "🔍 Checking Terraform installation..."
	@which terraform > /dev/null || (echo "❌ Terraform not found. Install from https://terraform.io/" && exit 1)
	@echo "✅ Terraform found: $$(terraform version | head -1)"

check-aws: check ## Check if AWS credentials are configured
	@$(MAKE) -s check-aws-smart

check-aws-smart: check ## Smart AWS credential checking with auto-setup
	@if [ -f ".aws-credentials" ]; then \
		echo "📁 Found cached credentials, loading..."; \
		source .aws-credentials; \
	fi; \
	if aws sts get-caller-identity > /dev/null 2>&1; then \
		echo "✅ AWS credentials are valid for account: $$(aws sts get-caller-identity --query Account --output text)"; \
	else \
		echo "🔄 AWS credentials not found or expired, setting up..."; \
		$(MAKE) -s setup-aws-credentials; \
	fi

setup-aws-credentials: ## Internal: Set up and cache AWS credentials
	@echo "🚀 Setting up AWS SSO credentials..."
	@echo "⚠️  This will open your browser for AWS SSO authentication"
	@if [ -z "$(AWS_PROFILE)" ]; then \
		if [ -f "../.secrets" ] && grep -q "^AWS_PROFILE=" "../.secrets"; then \
			echo "📁 Found AWS_PROFILE in .secrets file, please source it:"; \
			echo "  source ../.secrets && make aws-setup"; \
		else \
			cat <<'EOF' ; \
❌ Error: AWS_PROFILE not found in environment or ../.secrets file
Please set AWS_PROFILE:
  echo 'AWS_PROFILE=AdministratorAccess-123456789012' >> ../.secrets
  # then source it:
  source ../.secrets && make aws-setup
  # or set as environment variable:
  export AWS_PROFILE=AdministratorAccess-123456789012
EOF
		fi; \
		exit 1; \
	fi
	@aws sso login --profile $(AWS_PROFILE) || (echo "❌ AWS SSO login failed" && exit 1)
	@echo "💾 Exporting and caching credentials..."
	@aws configure export-credentials --profile $(AWS_PROFILE) --format env > .aws-credentials || (echo "❌ Failed to export credentials" && exit 1)
	@echo "# AWS Credentials cached at $$(date)" >> .aws-credentials
	@echo "# These will be automatically refreshed when expired" >> .aws-credentials
	@source .aws-credentials && aws sts get-caller-identity > /dev/null 2>&1 || (echo "❌ Credential validation failed" && exit 1)
	@echo "✅ AWS credentials successfully configured and cached"
	@echo "✅ Account: $$(source .aws-credentials && aws sts get-caller-identity --query Account --output text)"

# Advanced Commands
workspace-list: aws-setup ## List Terraform workspaces
	@echo "📁 Listing Terraform workspaces..."
	@source .aws-credentials && terraform workspace list

workspace-new: aws-setup ## Create new Terraform workspace (usage: make workspace-new NAME=myworkspace)
	@echo "📁 Creating new workspace: $(NAME)"
	@test -n "$(NAME)" || (echo "❌ Please specify NAME=workspace_name" && exit 1)
	@source .aws-credentials && terraform workspace new $(NAME)

workspace-select: aws-setup ## Select Terraform workspace (usage: make workspace-select NAME=myworkspace)
	@echo "📁 Selecting workspace: $(NAME)"
	@test -n "$(NAME)" || (echo "❌ Please specify NAME=workspace_name" && exit 1)
	@source .aws-credentials && terraform workspace select $(NAME)

state-list: aws-setup ## List resources in Terraform state
	@echo "📋 Listing Terraform state resources..."
	@source .aws-credentials && terraform state list

state-show: aws-setup ## Show specific resource from state (usage: make state-show RESOURCE=aws_instance.example)
	@echo "👀 Showing resource: $(RESOURCE)"
	@test -n "$(RESOURCE)" || (echo "❌ Please specify RESOURCE=resource_name" && exit 1)
	@source .aws-credentials && terraform state show $(RESOURCE)

# Development helpers
dev-setup: check aws-setup init validate ## Complete development setup
	@echo "🎯 Development environment ready!"
	@echo "   Next: make plan (to see what will be created)"

ci-check: check validate fmt ## CI/CD validation checks
	@echo "🤖 Running CI validation..."
	@terraform fmt -check -recursive || (echo "❌ Files need formatting. Run 'make fmt'" && exit 1)
	@echo "✅ All CI checks passed"
