resource "aws_s3_bucket" "backend_deploy" {
    bucket        = var.bucket_name
    force_destroy = var.force_destroy

    tags = merge(var.tags, {
        Environment = var.environment
        Project     = var.project
        CostCenter  = "solo-developer"
        Purpose     = "backend-deployment-artifacts"
    })
}

resource "aws_s3_bucket_versioning" "backend_deploy" {
    bucket = aws_s3_bucket.backend_deploy.id

    versioning_configuration {
        status = "Enabled"
    }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "backend_deploy" {
    bucket = aws_s3_bucket.backend_deploy.id

    rule {
        apply_server_side_encryption_by_default {
            sse_algorithm = "AES256"
        }
    }
}

resource "aws_s3_bucket_public_access_block" "backend_deploy" {
    bucket = aws_s3_bucket.backend_deploy.id

    block_public_acls       = true
    block_public_policy     = true
    ignore_public_acls      = true
    restrict_public_buckets = true
}
