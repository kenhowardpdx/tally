variable "aws_region" {
  description = "AWS region for API Gateway invoke URL."
  type        = string
}
variable "lambda_function_arn" {
  description = "ARN of the Lambda function to integrate with API Gateway."
  type        = string
}

variable "stage_name" {
  description = "Deployment stage name."
  type        = string
  default     = "prod"
}

variable "api_name" {
  description = "Name of the API Gateway REST API."
  type        = string
  default     = "tally-api"
}
