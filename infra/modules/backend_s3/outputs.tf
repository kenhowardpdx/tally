output "bucket_name" {
  description = "Name of the S3 bucket for backend assets"
  value       = aws_s3_bucket.backend_deploy.id
}

output "bucket_arn" {
  description = "ARN of the S3 bucket for backend assets"
  value       = aws_s3_bucket.backend_deploy.arn
}

output "bucket_domain_name" {
  description = "Domain name of the S3 bucket"
  value       = aws_s3_bucket.backend_deploy.bucket_domain_name
}
