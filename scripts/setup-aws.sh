#!/bin/zsh

# AWS Setup Script - sources credentials into current shell
# Usage: source ./setup-aws.sh [profile-name]

# Try to load AWS_PROFILE from .secrets file if not already set
if [[ -z "$AWS_PROFILE" && -f ".secrets" ]]; then
    echo "🔍 Loading AWS_PROFILE from .secrets file..."
    source .secrets
fi

# Check if AWS_PROFILE is set (after trying to load from .secrets)
if [[ -z "$AWS_PROFILE" && -z "$1" ]]; then
    echo "❌ Error: AWS_PROFILE not found in environment, .secrets file, or command arguments"
    echo "Please either:"
    echo "  1. Add to .secrets file: echo 'AWS_PROFILE=AdministratorAccess-123456789012' >> .secrets"
    echo "  2. Set environment variable: export AWS_PROFILE=AdministratorAccess-123456789012"
    echo "  3. Provide as argument: source ./setup-aws.sh AdministratorAccess-123456789012"
    return 1
fi

# Use provided profile or AWS_PROFILE environment variable (now potentially from .secrets)
PROFILE="${1:-$AWS_PROFILE}"

echo "Setting up AWS credentials..."

# Check if we're being sourced (not executed)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "❌ Error: This script must be sourced, not executed directly."
    echo "Usage: source ./setup-aws.sh"
    echo "   or: . ./setup-aws.sh"
    exit 1
fi

# Authenticate with SSO (will prompt if not already logged in)
aws sso login --profile "$PROFILE"

# Export credentials to environment
CREDS_FILE="$HOME/.aws-creds.env"
aws configure export-credentials --profile "$PROFILE" --format env > "$CREDS_FILE"
source "$CREDS_FILE"

# Verify credentials are working
if aws sts get-caller-identity >/dev/null 2>&1; then
    echo "✅ AWS credentials successfully configured for profile: $PROFILE"
    echo "You can now run terraform and other AWS commands."
else
    echo "❌ Failed to configure AWS credentials"
    return 1
fi
