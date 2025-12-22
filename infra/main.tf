module "backend_s3" {
  source      = "./modules/backend_s3"
  environment = var.environment
  project     = var.project
  bucket_name = "${var.project}-backend-${var.environment}-${var.aws_account_id}-${var.aws_region}"
  tags = {
    Environment = var.environment
    Project     = var.project
    Purpose     = "lambda-artifacts"
    CostCenter  = "solo-developer"
  }
}
terraform {
  # Trigger workflow: Copilot 2025-10-14
  required_version = ">= 1.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
    neon = {
      source  = "kislerdm/neon"
      version = "~> 0.6"
    }
  }
}

provider "aws" {
  alias   = "us_east_1"
  region  = "us-east-1"
  profile = var.aws_profile

  # Only ACM module should use the us-east-1 provider override
}

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile

  # Alternatively, use environment variables AWS_PROFILE or AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY
  # The setup-aws.sh script exports credentials to environment variables
}

# Neon provider configuration
# Set NEON_API_KEY environment variable or use provider block with api_key
provider "neon" {
  # api_key is read from NEON_API_KEY environment variable
  # Get your API key from: https://console.neon.tech/app/settings/api-keys
}

# VPC Module - Zero-Cost Network Foundation
module "vpc" {
  source = "./modules/vpc"

  vpc_cidr           = "10.0.0.0/20"
  environment        = var.environment
  project            = var.project
  availability_zones = ["${var.aws_region}a", "${var.aws_region}b"]

  # NAT Gateway disabled for zero-cost architecture
  # Lambda functions will run in public subnets with security groups
}

module "frontend_s3" {
  source                      = "./modules/frontend_s3"
  bucket_name                 = "${var.project}-frontend-${var.environment}-${var.aws_account_id}"
  aws_account_id              = var.aws_account_id
  cloudfront_distribution_arn = module.cloudfront.cloudfront_distribution_arn
  tags = {
    Environment = var.environment
    Project     = var.project
    Purpose     = "frontend-static-site"
    CostCenter  = "solo-developer"
  }
}

# ACM certificate for CloudFront custom domain (production only)
module "acm" {
  count                     = var.environment == "prod" ? 1 : 0
  source                    = "./modules/acm"
  domain_name               = "tally.kenhoward.dev"
  subject_alternative_names = []
  validation_method         = "DNS"
  providers = {
    aws = aws.us_east_1
  }
  tags = {
    Environment = var.environment
    Project     = var.project
    Purpose     = "cloudfront-ssl"
  }
}
module "cloudfront" {
  source                  = "./modules/cloudfront"
  bucket_name             = "${var.project}-frontend-${var.environment}-${var.aws_account_id}"
  aliases                 = var.environment == "prod" ? ["tally.kenhoward.dev"] : []
  acm_certificate_arn     = var.environment == "prod" ? module.acm[0].acm_certificate_arn : null
  api_gateway_domain_name = replace(replace(module.api_gateway.invoke_url, "https://", ""), "/${var.environment}", "")
  api_gateway_stage       = var.environment
  api_path_pattern        = "/api/v1/*"
  tags = {
    Environment = var.environment
    Project     = var.project
    Purpose     = "frontend-static-site"
    CostCenter  = "solo-developer"
  }
}

module "lambda" {
  source                   = "./modules/lambda"
  vpc_id                   = module.vpc.vpc_id
  public_subnet_ids        = module.vpc.public_subnet_ids
  lambda_security_group_id = module.vpc.lambda_security_group_id

  project     = var.project
  environment = var.environment

  # Neon database connection
  db_name     = module.neon.database_name
  db_username = module.neon.database_username
  db_password = module.neon.database_password
  db_host     = module.neon.database_host

  lambda_code_s3_bucket = module.backend_s3.bucket_name
}

# Neon Serverless PostgreSQL
# Free tier: 0.5 GB storage, scales to zero when idle
# Architecture: One shared project (super-water-91030697) with multiple branches
module "neon" {
  source = "./modules/neon"

  environment       = var.environment
  neon_project_id   = var.neon_project_id
  db_name           = "${var.project}db"
  db_username       = "${var.project}admin"

  # Auto-scales to 0.25 CU minimum, suspends after 5 minutes of inactivity
}

module "api_gateway" {
  source               = "./modules/api_gateway"
  lambda_function_arn  = module.lambda.backend_lambda_function_arn
  lambda_function_name = module.lambda.backend_lambda_function_name
  stage_name           = var.environment
  api_name             = "tally-api"
  aws_region           = var.aws_region
}

# Route53 DNS records (production only)
module "route53" {
  count                  = var.environment == "prod" ? 1 : 0
  source                 = "./modules/route53"
  cloudfront_domain_name = module.cloudfront.cloudfront_domain_name
  domain_name            = "kenhoward.dev"
}
