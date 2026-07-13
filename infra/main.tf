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

locals {
  frontend_domain = "tally.kenhoward.dev"

  # module.api_gateway.invoke_url looks like "https://<id>.execute-api.<region>.amazonaws.com/<stage>".
  # The REST API id/region aren't available anywhere else, so the domain has to come
  # from this URL. The stage segment is always var.environment (module.api_gateway is
  # called with stage_name = var.environment below) - used directly rather than
  # re-parsed back out of the URL for the same value.
  api_gateway_domain_name = split("/", replace(module.api_gateway.invoke_url, "https://", ""))[0]
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
  domain_name               = local.frontend_domain
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
  aliases                 = [local.frontend_domain]
  acm_certificate_arn     = module.acm.acm_certificate_arn
  api_gateway_domain_name = local.api_gateway_domain_name
  api_origin_path         = "/${var.environment}"
  api_path_pattern        = "/api/v1/*"
  tags = {
    Environment = var.environment
    Project     = var.project
    Purpose     = "frontend-static-site"
    CostCenter  = "solo-developer"
  }
}

module "lambda" {
  source  = "./modules/lambda"
  project = var.project

  database_url_readwrite = var.database_url_readwrite
  database_url_readonly  = var.database_url_readonly
  auth0_domain           = var.auth0_domain
  auth0_audience         = var.auth0_audience

  lambda_code_s3_bucket = module.backend_s3.bucket_name
}


module "api_gateway" {
  source              = "./modules/api_gateway"
  lambda_function_arn = module.lambda.backend_lambda_function_arn
  stage_name          = var.environment
  api_name            = "tally-api"
  aws_region          = var.aws_region
}
