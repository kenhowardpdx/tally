#!/bin/zsh

# AWS Setup Script - sources credentials into current shell
# Usage: source ./setup-aws.sh

PROFILE="AdministratorAccess-123456789012"

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
