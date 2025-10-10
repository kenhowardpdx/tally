# Route53 Module
# Define your Route53 hosted zone and DNS records here
resource "aws_route53_zone" "this" {
  # ...hosted zone configuration...
}

output "domain_name" {
  value = aws_route53_zone.this.name
}
