# Route53 Module
# Define your Route53 hosted zone and DNS records here
resource "aws_route53_zone" "this" {
  name = var.domain_name
}

output "domain_name" {
  value = aws_route53_zone.this.name
}

output "name_servers" {
  description = "Route 53 hosted zone name servers"
  value       = aws_route53_zone.this.name_servers
}

# DNS record for tally.kenhoward.dev pointing to S3 website endpoint
resource "aws_route53_record" "frontend" {
  zone_id = aws_route53_zone.this.zone_id
  name    = "tally.kenhoward.dev"
  type    = "CNAME"
  ttl     = 300
  records = [var.cloudfront_domain_name]
}
