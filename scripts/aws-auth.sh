#!/usr/bin/env bash
# scripts/aws-auth.sh - Authenticate with AWS SSO
#
# Usage:
#   ./scripts/aws-auth.sh          - SSO login only (for direct terraform use)
#   ./scripts/aws-auth.sh --creds  - SSO login + export STS creds for ACT

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SECRETS_FILE="$SCRIPT_DIR/../.secrets"

# Load AWS_PROFILE from .secrets if not already set
if [[ -z "${AWS_PROFILE:-}" && -f "$SECRETS_FILE" ]]; then
    AWS_PROFILE=$(grep '^AWS_PROFILE=' "$SECRETS_FILE" | cut -d'=' -f2)
fi

if [[ -z "${AWS_PROFILE:-}" ]]; then
    echo "❌ AWS_PROFILE not set. Add 'AWS_PROFILE=<profile>' to .secrets or export it."
    exit 1
fi

echo "Logging in with profile: $AWS_PROFILE"
aws sso login --profile "$AWS_PROFILE"

if ! aws sts get-caller-identity --profile "$AWS_PROFILE" >/dev/null 2>&1; then
    echo "❌ AWS auth failed"
    exit 1
fi

echo "✅ SSO login successful"

if [[ "${1:-}" != "--creds" ]]; then
    echo "Tip: run 'make aws-creds' to also export static credentials for ACT."
    exit 0
fi

echo "Exporting STS credentials..."

CREDS=$(aws configure export-credentials --profile "$AWS_PROFILE" --format env-no-export)
KEY=$(echo "$CREDS" | grep '^AWS_ACCESS_KEY_ID=' | cut -d'=' -f2)
SECRET=$(echo "$CREDS" | grep '^AWS_SECRET_ACCESS_KEY=' | cut -d'=' -f2)
TOKEN=$(echo "$CREDS" | grep '^AWS_SESSION_TOKEN=' | cut -d'=' -f2)
EXPIRY=$(echo "$CREDS" | grep '^AWS_CREDENTIAL_EXPIRATION=' | cut -d'=' -f2)

# Update ~/.aws/credentials [default] section
{
    echo "[default]"
    echo "aws_access_key_id=$KEY"
    echo "aws_secret_access_key=$SECRET"
    echo "aws_session_token=$TOKEN"
} > "$HOME/.aws/credentials"

# Update only credential vars in .secrets, preserving everything else
if [[ -f "$SECRETS_FILE" ]]; then
    TMPFILE=$(mktemp)
    grep -v "^AWS_ACCESS_KEY_ID=\|^AWS_SECRET_ACCESS_KEY=\|^AWS_SESSION_TOKEN=" "$SECRETS_FILE" > "$TMPFILE"
    {
        echo "AWS_ACCESS_KEY_ID=$KEY"
        echo "AWS_SECRET_ACCESS_KEY=$SECRET"
        echo "AWS_SESSION_TOKEN=$TOKEN"
    } >> "$TMPFILE"
    mv "$TMPFILE" "$SECRETS_FILE"
fi

echo "✅ Credentials exported (expire: $EXPIRY)"
