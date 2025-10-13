# Tally Project Makefile
# This Makefile provides common development tasks and GitHub Actions testing

.PHONY: help github_workflow_terraform-pr github_workflow_ci

# Default target
help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# GitHub workflow testing with act
.github_workflow_%:
	@if [ ! -f .github/workflows/$*.yml ]; then \
		echo "Error: Workflow '.github/workflows/$*.yml' not found"; \
		ls -1 .github/workflows/*.yml | sed 's|.github/workflows/||' | sed 's|\.yml$$||'; \
		exit 1; \
	fi
	@if [ -z "$$AWS_PROFILE" ] && ! grep -q "^AWS_PROFILE=" .secrets 2>/dev/null; then \
		echo "Error: AWS_PROFILE not found. Add to .secrets or environment."; \
		exit 1; \
	fi
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
	@ls -1 .github/workflows/*.yml | sed 's|.github/workflows/||' | sed 's|\.yml$$||' | sed 's/^/github_workflow_/'

# Pre-commit validation
pre-commit: ## Run all pre-commit validations
	@$(MAKE) validate-actions

# GitHub Actions validation
validate-actions: ## Validate GitHub Actions versions against approved list
	@./scripts/validate-actions.sh

show-action-versions: ## Display all approved GitHub Actions versions
	@maxlen=$$(grep -v "^#" .github/action-versions.conf | grep -v "^$$" | awk -F':' '{print length($$1)}' | sort -nr | head -n1); \
	grep -v "^#" .github/action-versions.conf | grep -v "^$$" | while IFS=':' read -r action version; do \
		printf "%-$${maxlen}s %s\n" "$$action" "$$version"; \
	done

show-current-usage: ## Show which action versions are currently used in workflows
	@find .github/workflows -name "*.yml" -o -name "*.yaml" | while read -r file; do \
		echo "$$file:"; \
		grep -n "uses:" "$$file" | sed 's/^/  /' || true; \
		echo ""; \
	done

install-git-hooks: ## Install git hooks for pre-commit validation
	@mkdir -p .git/hooks
	@echo '#!/bin/bash' > .git/hooks/pre-commit
	@echo 'make pre-commit' >> .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@echo "Git hooks installed"

uninstall-git-hooks: ## Remove git hooks
	@rm -f .git/hooks/pre-commit
	@echo "Git hooks removed"
