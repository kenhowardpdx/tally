# Lambda Module
# Define your Lambda function and IAM role here
resource "aws_lambda_function" "this" {
  # ...lambda configuration...
}

output "lambda_function_arn" {
  value = aws_lambda_function.this.arn
}
