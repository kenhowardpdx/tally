resource "aws_route53_zone" "this" {
  name = var.domain_name
}

resource "aws_route53_record" "frontend" {
  zone_id = aws_route53_zone.this.zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = var.cloudfront_domain_name
    zone_id                = var.cloudfront_hosted_zone_id
    evaluate_target_health = false
  }
}

output "domain_name" {
  value = aws_route53_zone.this.name
}

output "name_servers" {
  description = "Add these as NS records in Hover for the subdomain to delegate DNS to Route 53"
  value       = aws_route53_zone.this.name_servers
}

