terraform {
  required_version = ">= 1.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
  backend "s3" {
    bucket  = "terraform-state-123456789012"
    key     = "tally/prod/terraform.tfstate"
    region  = "us-west-2"
    encrypt = true
  }
}

provider "aws" {
  region  = var.aws_region
  profile = "AdministratorAccess-123456789012"

  # Alternatively, the setup-aws.sh script exports credentials to environment variables
  # so you can also omit the profile if you source the script first
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
