data "aws_cloudfront_cache_policy" "caching_disabled" {
  name = "Managed-CachingDisabled"
}

data "aws_cloudfront_origin_request_policy" "all_viewer_except_host_header" {
  name = "Managed-AllViewerExceptHostHeader"
}

resource "aws_cloudfront_origin_access_control" "s3_oac" {
  name                              = "${var.bucket_name}-oac"
  description                       = "OAC for S3 static site"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "frontend" {
  depends_on          = [var.acm_certificate_arn]
  enabled             = true
  default_root_object = "index.html"

  origin {
    domain_name              = "${var.bucket_name}.s3.amazonaws.com"
    origin_id                = "s3-frontend"
    origin_access_control_id = aws_cloudfront_origin_access_control.s3_oac.id
  }

  origin {
    domain_name = var.api_gateway_domain_name
    origin_id   = "api-gateway"
    origin_path = var.api_origin_path
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "s3-frontend"
    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
  }

  ordered_cache_behavior {
    path_pattern           = var.api_path_pattern
    allowed_methods        = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods         = ["GET", "HEAD", "OPTIONS"]
    target_origin_id       = "api-gateway"
    viewer_protocol_policy = "redirect-to-https"

    # Managed-CachingDisabled: this behavior proxies a live API, not cacheable content.
    cache_policy_id = data.aws_cloudfront_cache_policy.caching_disabled.id

    # Managed-AllViewerExceptHostHeader: forwards all headers/cookies/query strings
    # except Host. API Gateway's execute-api domain is itself fronted by AWS's shared
    # edge network, and forwarding the viewer's Host header (tally.kenhoward.dev, a
    # registered CloudFront alias) collides with that routing, causing
    # misdirected-request errors instead of reaching the Lambda backend.
    origin_request_policy_id = data.aws_cloudfront_origin_request_policy.all_viewer_except_host_header.id
  }

  aliases     = var.aliases
  price_class = "PriceClass_100"

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn            = var.acm_certificate_arn
    ssl_support_method             = "sni-only"
    minimum_protocol_version       = "TLSv1.2_2021"
    cloudfront_default_certificate = var.acm_certificate_arn == null ? true : false
  }

  tags = var.tags
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.frontend.domain_name
}

output "cloudfront_distribution_arn" {
  description = "CloudFront distribution ARN"
  value       = aws_cloudfront_distribution.frontend.arn
}
