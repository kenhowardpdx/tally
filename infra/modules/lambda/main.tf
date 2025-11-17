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

# Attach AWS managed policies for Lambda execution, VPC, S3, and RDS access
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_vpc_access" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_s3_read" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
}

resource "aws_iam_role_policy_attachment" "lambda_rds_access" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonRDSFullAccess"
}

# Placeholder for Lambda build artifact
resource "null_resource" "lambda_build_placeholder" {
  provisioner "local-exec" {
    command = "echo 'Lambda build not yet uploaded. This is a placeholder.'"
  }
}

# resource "aws_lambda_function" "backend" {
#   function_name = "${var.project}-backend"
#   handler       = "main.handler"
#   runtime       = "python3.13"
#   s3_bucket     = var.lambda_code_s3_bucket
#   s3_key        = "backend"
#   role          = aws_iam_role.lambda_exec.arn
#
#   vpc_config {
#     subnet_ids         = var.public_subnet_ids
#     security_group_ids = [var.lambda_security_group_id]
#   }
#
#   environment {
#     variables = {
#       DB_NAME     = var.db_name
#       DB_USERNAME = var.db_username
#       DB_PASSWORD = var.db_password
#       DB_HOST     = var.db_host
#     }
#   }
# }

# output "backend_lambda_function_arn" {
#   value = aws_lambda_function.backend.arn
# }

output "lambda_exec_role_arn" {
  value = aws_iam_role.lambda_exec.arn
}
