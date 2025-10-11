# Tally Project Makefile
# This Makefile provides common development tasks and GitHub Actions testing

.PHONY: help github_workflow_terraform-pr github_workflow_ci

# Default target
help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# GitHub workflow testing with act
.github_workflow_%:
	@echo "Running GitHub Actions workflow: $*"
	@if [ ! -f .github/workflows/$*.yml ]; then \
		echo "Error: Workflow file '.github/workflows/$*.yml' not found"; \
		echo "Available workflows:"; \
		ls -1 .github/workflows/*.yml | sed 's|.github/workflows/||' | sed 's|\.yml$$||'; \
		exit 1; \
	fi
	@if [ -z "$$AWS_PROFILE" ] && ! grep -q "^AWS_PROFILE=" .secrets 2>/dev/null; then \
		echo "Error: AWS_PROFILE not found in environment or .secrets file"; \
		echo "Please add AWS_PROFILE to your .secrets file:"; \
		echo "  echo 'AWS_PROFILE=AdministratorAccess-123456789012' >> .secrets"; \
		echo "  # or set as environment variable:"; \
		echo "  export AWS_PROFILE=AdministratorAccess-123456789012"; \
		exit 1; \
	fi
	@echo "Using local AWS credentials and environment..."
	act pull_request \
		--secret-file .secrets \
		--container-options "-v $(HOME)/.aws:/root/.aws:ro" \
		--env AWS_DEFAULT_REGION=us-west-2 \
		--env ACT=true \
		-W .github/workflows/$*.yml

# Specific workflow targets for convenience
github_workflow_terraform-pr: ## Run the Terraform PR validation workflow
	@$(MAKE) .github_workflow_terraform-pr

github_workflow_ci: ## Run the CI workflow
	@$(MAKE) .github_workflow_ci

# List available workflows
list-workflows: ## List all available GitHub workflows
	@echo "Available GitHub workflows:"
	@ls -1 .github/workflows/*.yml | sed 's|.github/workflows/||' | sed 's|\.yml$$||' | sed 's/^/  - github_workflow_/'
