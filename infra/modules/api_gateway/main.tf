# API Gateway Module
# Define your API Gateway REST API, resources, and integrations here
resource "aws_api_gateway_rest_api" "this" {
  # ...api gateway configuration...
}

output "invoke_url" {
  value = aws_api_gateway_rest_api.this.execution_arn
}
