#!/usr/bin/env bash
# scripts/export-aws-credentials.sh
# Export AWS SSO credentials to ~/.aws/credentials in INI format for Terraform/ACT

set -e
source ../.secrets
PROFILE="$AWS_PROFILE"
CRED_FILE="$HOME/.aws/credentials"

aws sso login --profile "$PROFILE"
aws configure export-credentials --profile "$PROFILE" --format env | awk '
  /^AWS_ACCESS_KEY_ID=/ { print "aws_access_key_id=" $2 }
  /^AWS_SECRET_ACCESS_KEY=/ { print "aws_secret_access_key=" $2 }
  /^AWS_SESSION_TOKEN=/ { print "aws_session_token=" $2 }
' > "$CRED_FILE.tmp"

# Add [default] at the top
{ echo "[default]"; cat "$CRED_FILE.tmp"; } > "$CRED_FILE"
rm "$CRED_FILE.tmp"

echo "Exported credentials to $CRED_FILE in INI format."
