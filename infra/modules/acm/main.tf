# ACM Module
# Define your ACM certificate for the custom domain here
resource "aws_acm_certificate" "this" {
  # ...certificate configuration...
}

output "certificate_arn" {
  value = aws_acm_certificate.this.arn
}
