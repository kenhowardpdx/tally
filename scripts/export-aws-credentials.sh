#!/usr/bin/env bash
# scripts/export-aws-credentials.sh
# Export AWS SSO credentials to ~/.aws/credentials in INI format for Terraform/ACT

set -e
source .secrets
PROFILE="$AWS_PROFILE"
CRED_FILE="$HOME/.aws/credentials"

aws sso login --profile "$PROFILE"
aws configure export-credentials --profile "$PROFILE" --format env > "$CRED_FILE.env"

AWS_ACCESS_KEY_ID=$(grep '^export AWS_ACCESS_KEY_ID=' "$CRED_FILE.env" | cut -d'=' -f2)
AWS_SECRET_ACCESS_KEY=$(grep '^export AWS_SECRET_ACCESS_KEY=' "$CRED_FILE.env" | cut -d'=' -f2)
# Multiline session token
AWS_SESSION_TOKEN=$(awk '/^export AWS_SESSION_TOKEN=/{flag=1;print substr($0,25);next}/^export AWS_CREDENTIAL_EXPIRATION=/{flag=0}flag{print}' "$CRED_FILE.env")

# Write INI format for Terraform/SDKs
{
	echo "[default]"
	echo "aws_access_key_id=$AWS_ACCESS_KEY_ID"
	echo "aws_secret_access_key=$AWS_SECRET_ACCESS_KEY"
	echo "aws_session_token=$AWS_SESSION_TOKEN"
} > "$CRED_FILE"

# Write environment variables for ACT workflow
{
	echo "AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID"
	echo "AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY"
	echo "AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN"
} > .secrets

rm "$CRED_FILE.env"

echo "Exported credentials to $CRED_FILE in INI format and .secrets for ACT."
