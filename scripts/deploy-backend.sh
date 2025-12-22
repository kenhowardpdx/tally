#!/usr/bin/env bash
# Deploy Backend Lambda Function
# Usage: ./scripts/deploy-backend.sh [environment]
#
# Packages and deploys the Python backend Lambda function
# Environment defaults to 'dev' for local deployments

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

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

echo -e "${GREEN}Backend Lambda Deployment${NC}"
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

cd "$BACKEND_DIR"

# Install dependencies if needed
if [[ ! -d ".venv" ]] || [[ ! -f "poetry.lock" ]]; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    poetry install --no-dev
fi

# Create deployment package
echo -e "${YELLOW}Creating deployment package...${NC}"
DIST_DIR="$BACKEND_DIR/dist"
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"

# Copy application code
cp -r src/* "$DIST_DIR/"

# Package into zip
cd "$DIST_DIR"
ZIP_FILE="lambda_function.zip"
zip -r "$ZIP_FILE" . -x "*.pyc" -x "__pycache__/*"

echo -e "${GREEN}Package created: $DIST_DIR/$ZIP_FILE${NC}"

# Upload to S3
S3_BUCKET="tally-backend-${ENVIRONMENT}-${AWS_ACCOUNT_ID}-${AWS_REGION}"
S3_KEY="lambda_function.zip"

echo -e "${YELLOW}Uploading to S3: s3://${S3_BUCKET}/${S3_KEY}${NC}"
aws s3 cp "$ZIP_FILE" "s3://${S3_BUCKET}/${S3_KEY}" \
    --region "$AWS_REGION" \
    --profile "${AWS_PROFILE}"

# Update Lambda function
LAMBDA_FUNCTION_NAME="tally-${ENVIRONMENT}-backend"

echo -e "${YELLOW}Updating Lambda function: ${LAMBDA_FUNCTION_NAME}${NC}"
aws lambda update-function-code \
    --function-name "$LAMBDA_FUNCTION_NAME" \
    --s3-bucket "$S3_BUCKET" \
    --s3-key "$S3_KEY" \
    --region "$AWS_REGION" \
    --profile "${AWS_PROFILE}" \
    > /dev/null

echo ""
echo -e "${GREEN}✓ Backend deployed successfully!${NC}"
echo ""
echo "Function: $LAMBDA_FUNCTION_NAME"
echo "Region: $AWS_REGION"
echo "Package: s3://${S3_BUCKET}/${S3_KEY}"
