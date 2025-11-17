output "backend_lambda_function_arn" {
  value = aws_lambda_function.backend.arn
}

output "lambda_exec_role_arn" {
  value = aws_iam_role.lambda_exec.arn
}
