resource "aws_s3_bucket" "frontend" {
  bucket        = var.bucket_name
  force_destroy = true
  tags          = var.tags
}

# Belt-and-suspenders alongside the SourceArn-scoped bucket policy below: the
# policy only ever grants CloudFront's service principal access (not "public"
# in AWS's sense, so Block Public Access doesn't interfere with it), but an
# explicit block still guards against a future accidental public ACL/policy
# on this bucket. Matches backend_s3's posture (see modules/backend_s3/main.tf).
resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


resource "aws_s3_bucket_website_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  index_document {
    suffix = "index.html"
  }
  error_document {
    key = "index.html"
  }
}


# Secure bucket policy for CloudFront OAC

resource "aws_s3_bucket_policy" "frontend_cloudfront" {
  bucket = aws_s3_bucket.frontend.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "cloudfront.amazonaws.com"
        },
        Action   = ["s3:GetObject"],
        Resource = ["${aws_s3_bucket.frontend.arn}/*"],
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = var.cloudfront_distribution_arn
          }
        }
      }
    ]
  })
}

