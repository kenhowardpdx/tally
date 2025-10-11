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

# Placeholder modules - commented out until implementation
# Uncomment and configure these modules as you implement each component

# module "lambda" {
#   source = "./modules/lambda"
#   # Add lambda module variables here
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
