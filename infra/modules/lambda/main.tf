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

# Attach AWS managed policies for Lambda execution and S3 access
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}


resource "aws_iam_role_policy_attachment" "lambda_s3_read" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
}


locals {
  # PR validation plans backend/infra changes without building backend.zip first,
  # so fall back to null there rather than failing terraform plan.
  backend_zip_path = "${path.module}/../../backend.zip"
  backend_zip_hash = fileexists(local.backend_zip_path) ? filebase64sha256(local.backend_zip_path) : null
}

resource "aws_lambda_function" "backend" {
  function_name    = "${var.project}-backend"
  handler          = "main.handler"
  runtime          = "python3.13"
  s3_bucket        = var.lambda_code_s3_bucket
  s3_key           = "backend.zip"
  source_code_hash = local.backend_zip_hash
  role             = aws_iam_role.lambda_exec.arn

  environment {
    variables = {
      DATABASE_URL_READWRITE = var.database_url_readwrite
      DATABASE_URL_READONLY  = var.database_url_readonly
    }
  }
}

