# S3 Module - Document Storage

# -----------------------------------------------------------------------------
# Input Bucket (for document uploads)
# -----------------------------------------------------------------------------

resource "aws_s3_bucket" "input" {
  bucket        = "${var.project_name}-input-${var.environment}"
  force_destroy = var.force_destroy

  tags = {
    Name    = "${var.project_name}-input-${var.environment}"
    Purpose = "Document uploads for ingestion"
  }
}

# -----------------------------------------------------------------------------
# Output Bucket (for processed documents)
# -----------------------------------------------------------------------------

resource "aws_s3_bucket" "output" {
  bucket        = "${var.project_name}-output-${var.environment}"
  force_destroy = var.force_destroy

  tags = {
    Name    = "${var.project_name}-output-${var.environment}"
    Purpose = "Processed document results"
  }
}

# Encryption

resource "aws_s3_bucket_server_side_encryption_configuration" "input" {
  bucket = aws_s3_bucket.input.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "output" {
  bucket = aws_s3_bucket.output.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# -----------------------------------------------------------------------------
# Public Access Block (security best practice)
# -----------------------------------------------------------------------------

resource "aws_s3_bucket_public_access_block" "input" {
  bucket = aws_s3_bucket.input.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "output" {
  bucket = aws_s3_bucket.output.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# -----------------------------------------------------------------------------
# Versioning (optional - disabled by default for cost savings)
# -----------------------------------------------------------------------------

resource "aws_s3_bucket_versioning" "input" {
  bucket = aws_s3_bucket.input.id

  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Suspended"
  }
}

resource "aws_s3_bucket_versioning" "output" {
  bucket = aws_s3_bucket.output.id

  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Suspended"
  }
}

# -----------------------------------------------------------------------------
# Lifecycle Rules - Data Retention / Cost Optimization
# -----------------------------------------------------------------------------

resource "aws_s3_bucket_lifecycle_configuration" "input" {
  bucket = aws_s3_bucket.input.id

  rule {
    id     = "cleanup-old-uploads"
    status = var.lifecycle_days_to_expire > 0 ? "Enabled" : "Disabled"

    filter {} # Apply to all objects

    # Delete old uploaded documents after N days
    expiration {
      days = var.lifecycle_days_to_expire
    }

    # Clean up incomplete multipart uploads (saves storage costs)
    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "output" {
  bucket = aws_s3_bucket.output.id

  rule {
    id     = "cleanup-processed-docs"
    status = var.lifecycle_days_to_expire > 0 ? "Enabled" : "Disabled"

    filter {} # Apply to all objects

    # Delete processed documents after N days
    expiration {
      days = var.lifecycle_days_to_expire
    }

    # Clean up incomplete multipart uploads
    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  # Optional: Archive to Glacier for long-term storage
  dynamic "rule" {
    for_each = var.lifecycle_days_to_archive > 0 ? [1] : []
    content {
      id     = "archive-to-glacier"
      status = "Enabled"

      filter {} # Apply to all objects

      transition {
        days          = var.lifecycle_days_to_archive
        storage_class = "GLACIER"
      }
    }
  }
}
