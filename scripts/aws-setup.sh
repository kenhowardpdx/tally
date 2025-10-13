#!/usr/bin/env bash
# scripts/aws-setup.sh
# Usage: ./scripts/aws-setup.sh
# Sets up AWS SSO credentials for Terraform workflows

set -e

if [ ! -f "../.secrets" ]; then
  echo "❌ .secrets file required"
  exit 1
fi
set -a
source ../.secrets
set +a

if [ -z "$AWS_PROFILE" ]; then
  echo "❌ AWS_PROFILE required. Add to ../.secrets or export"
  exit 1
fi
aws sso login --profile "$AWS_PROFILE"
