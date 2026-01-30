# =============================================================================
# S3 Module Outputs
# =============================================================================

output "input_bucket_name" {
  description = "Name of the input S3 bucket"
  value       = aws_s3_bucket.input.bucket
}

output "input_bucket_arn" {
  description = "ARN of the input S3 bucket"
  value       = aws_s3_bucket.input.arn
}

output "input_bucket_id" {
  description = "ID of the input S3 bucket"
  value       = aws_s3_bucket.input.id
}

output "output_bucket_name" {
  description = "Name of the output S3 bucket"
  value       = aws_s3_bucket.output.bucket
}

output "output_bucket_arn" {
  description = "ARN of the output S3 bucket"
  value       = aws_s3_bucket.output.arn
}

output "output_bucket_id" {
  description = "ID of the output S3 bucket"
  value       = aws_s3_bucket.output.id
}
