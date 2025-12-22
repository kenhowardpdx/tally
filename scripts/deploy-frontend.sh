#!/usr/bin/env bash
# Deploy Frontend to S3
# Usage: ./scripts/deploy-frontend.sh [environment]
#
# Builds and deploys the Svelte frontend to the appropriate S3 bucket
# Environment defaults to 'dev' for local deployments

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Load environment from .secrets if available
if [[ -f "$PROJECT_ROOT/.secrets" ]]; then
    source "$PROJECT_ROOT/.secrets"
fi

# Default to dev environment for local deployments
ENVIRONMENT="${1:-${TF_VAR_environment:-dev}}"
AWS_REGION="${AWS_DEFAULT_REGION:-us-west-2}"
AWS_ACCOUNT_ID="${TF_VAR_aws_account_id}"

echo -e "${GREEN}Frontend Deployment${NC}"
echo "Environment: $ENVIRONMENT"
echo "Region: $AWS_REGION"
echo ""

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|prod)$ ]]; then
    echo -e "${RED}Error: Invalid environment '$ENVIRONMENT'${NC}"
    echo "Must be 'dev' or 'prod'"
    exit 1
fi

# Validate AWS credentials
if [[ -z "$AWS_ACCOUNT_ID" ]]; then
    echo -e "${RED}Error: AWS account ID not set${NC}"
    echo "Set TF_VAR_aws_account_id in .secrets file"
    exit 1
fi

cd "$FRONTEND_DIR"

# Check for yarn.lock
if [[ ! -f yarn.lock ]]; then
    echo -e "${RED}Error: yarn.lock not found${NC}"
    exit 1
fi

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
yarn install --frozen-lockfile

# Build frontend
echo -e "${YELLOW}Building frontend...${NC}"
yarn build

# Verify build output
if [[ ! -d build ]] || [[ -z "$(ls -A build)" ]]; then
    echo -e "${RED}Error: Build output missing or empty${NC}"
    exit 1
fi

# Sync to S3
BUCKET_NAME="tally-frontend-${ENVIRONMENT}-${AWS_ACCOUNT_ID}"
echo -e "${YELLOW}Deploying to s3://${BUCKET_NAME}...${NC}"

cd build
aws s3 sync . "s3://${BUCKET_NAME}/" \
    --region "$AWS_REGION" \
    --delete \
    --profile "${AWS_PROFILE:-default}" || {
    echo -e "${RED}Error: S3 sync failed${NC}"
    exit 1
}

echo -e "${GREEN}✓ Frontend deployed successfully${NC}"
echo ""
echo "Access your site at:"
if [[ "$ENVIRONMENT" == "prod" ]]; then
    echo "https://your-domain.com (when DNS configured)"
else
    # Get CloudFront domain from outputs
    cd "$PROJECT_ROOT/infra"
    CLOUDFRONT_DOMAIN=$(terraform output -raw cloudfront_domain_name 2>/dev/null || echo "")
    if [[ -n "$CLOUDFRONT_DOMAIN" ]]; then
        echo "https://${CLOUDFRONT_DOMAIN}"
    else
        echo "Run 'terraform output cloudfront_domain_name' in infra/ to get your URL"
    fi
fi
