terraform {
  required_version = ">= 1.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
  backend "s3" {
    # Backend configuration is provided via init command
    # Local: make init (uses .secrets)
    # GitHub Actions: uses repository secrets
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
  project_name       = "tally"
  availability_zones = ["${var.aws_region}a", "${var.aws_region}b"]
  
  # NAT Gateway disabled for zero-cost architecture
  # Lambda functions will run in public subnets with security groups
}

# Placeholder modules - commented out until implementation
# Uncomment and configure these modules as you implement each component

# module "lambda" {
#   source = "./modules/lambda"
#   vpc_id                     = module.vpc.vpc_id
#   public_subnet_ids          = module.vpc.public_subnet_ids
#   lambda_security_group_id   = module.vpc.lambda_security_group_id
# }

# module "rds" {
#   source = "./modules/rds"
#   vpc_id                  = module.vpc.vpc_id
#   database_subnet_ids     = module.vpc.database_subnet_ids
#   rds_security_group_id   = module.vpc.rds_security_group_id
# }

# module "api_gateway" {
#   source = "./modules/api_gateway"
#   # Add api_gateway module variables here
# }

# module "acm" {
#   source = "./modules/acm"
#   # Add acm module variables here
# }

# module "route53" {
#   source = "./modules/route53"
#   # Add route53 module variables here
# }

# module "auth0" {
#   source = "./modules/auth0"
#   # Add auth0 module variables here
# }
