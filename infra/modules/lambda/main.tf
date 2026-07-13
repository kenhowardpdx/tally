# Lambda Module
# IAM role for Lambda
resource "aws_iam_role" "lambda_exec" {
  name = "${var.project}-lambda-exec"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# CloudWatch Logs write access only. The Lambda deployment package is fetched
# by AWS's own Lambda service (s3_bucket/s3_key above) using its own
# infrastructure permissions, not by code running inside the function - the
# app itself never calls the S3 API (no boto3/S3 usage in backend/src), so the
# account-wide AmazonS3ReadOnlyAccess this previously carried was unused,
# unnecessary access to every bucket in the account (Phase 5 security review).
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}


locals {
  # PR validation plans backend/infra changes without building backend.zip first,
  # so fall back to null there rather than failing terraform plan.
  backend_zip_path = "${path.module}/../../backend.zip"
  backend_zip_hash = fileexists(local.backend_zip_path) ? filebase64sha256(local.backend_zip_path) : null
}

resource "aws_lambda_function" "backend" {
  function_name    = "${var.project}-backend"
  handler          = "src.main.handler"
  runtime          = "python3.13"
  s3_bucket        = var.lambda_code_s3_bucket
  s3_key           = "backend.zip"
  source_code_hash = local.backend_zip_hash
  role             = aws_iam_role.lambda_exec.arn

  # AWS defaults (3s timeout, 128MB memory) are too tight for a cold start:
  # importing FastAPI/SQLAlchemy/asyncpg plus Neon's own compute waking from
  # scale-to-zero suspend routinely takes longer than 3s, and API Gateway
  # surfaces that Lambda execution error as a 502 to the client. More memory
  # also means more CPU during init (Lambda allocates CPU proportional to
  # memory), which shortens the cold start itself, not just tolerates it.
  # Still well within the free tier's 400,000 GB-seconds/month at this
  # request volume - no provisioned concurrency, which is the actual
  # cold-start elimination fix but costs a flat monthly fee even when idle.
  timeout     = 15
  memory_size = 512

  environment {
    variables = {
      DATABASE_URL_READWRITE = var.database_url_readwrite
      DATABASE_URL_READONLY  = var.database_url_readonly
      AUTH0_DOMAIN           = var.auth0_domain
      AUTH0_AUDIENCE         = var.auth0_audience
    }
  }
}

