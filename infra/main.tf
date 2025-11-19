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
  }
}

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile

  # Alternatively, use environment variables AWS_PROFILE or AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY
  # The setup-aws.sh script exports credentials to environment variables
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

# ACM certificate for CloudFront custom domain
module "acm" {
  source                    = "./modules/acm"
  domain_name               = "tally.kenhoward.dev"
  subject_alternative_names = []
  validation_method         = "DNS"
  tags = {
    Environment = var.environment
    Project     = var.project
    Purpose     = "cloudfront-ssl"
  }
}
module "cloudfront" {
  source                  = "./modules/cloudfront"
  bucket_name             = "${var.project}-frontend-${var.environment}-${var.aws_account_id}"
  aliases                 = ["tally.kenhoward.dev"]
  acm_certificate_arn     = module.acm.acm_certificate_arn
  api_gateway_domain_name = replace(replace(module.api_gateway.invoke_url, "https://", ""), "/prod", "")
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

  project = var.project

  db_name     = module.rds.rds_db_name
  db_username = module.rds.rds_username
  db_password = data.aws_secretsmanager_secret_version.rds_password_version.secret_string
  db_host     = module.rds.rds_endpoint

  lambda_code_s3_bucket = module.backend_s3.bucket_name
}

data "aws_secretsmanager_secret" "rds_password" {
  name = "prod-rds-postgres-password"
}

data "aws_secretsmanager_secret_version" "rds_password_version" {
  secret_id = data.aws_secretsmanager_secret.rds_password.id
}

module "rds" {
  source             = "./modules/rds"
  db_name            = "${var.project}db"
  db_username        = "${var.project}admin"
  db_password        = data.aws_secretsmanager_secret_version.rds_password_version.secret_string
  db_subnet_group    = module.vpc.db_subnet_group
  security_group_ids = [module.vpc.rds_security_group_id]
  tags = {
    Environment = var.environment
    Project     = var.project
    Purpose     = "rds"
  }
  environment = var.environment
}

module "bastion" {
  source            = "./modules/bastion"
  subnet_id         = module.vpc.public_subnet_ids[0]
  security_group_id = module.vpc.lambda_security_group_id
  key_name          = "${var.project}-bastion-key-prod" # Project-specific SSH key name
  tags = {
    Environment = var.environment
    Project     = var.project
    Purpose     = "bastion"
  }
}

module "api_gateway" {
  source              = "./modules/api_gateway"
  lambda_function_arn = module.lambda.backend_lambda_function_arn
  stage_name          = "prod"
  api_name            = "tally-api"
  aws_region          = var.aws_region
}

# module "acm" {
#   source = "./modules/acm"
#   # Add acm module variables here
# }

module "route53" {
  source                 = "./modules/route53"
  cloudfront_domain_name = module.cloudfront.cloudfront_domain_name
  domain_name            = "kenhoward.dev"
}

# module "auth0" {
#   source = "./modules/auth0"
#   # Add auth0 module variables here
# }
