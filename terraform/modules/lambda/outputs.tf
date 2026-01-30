# =============================================================================
# Lambda Module Outputs
# =============================================================================

output "ingestion_lambda_arn" {
  description = "ARN of the ingestion Lambda function"
  value       = aws_lambda_function.ingestion.arn
}

output "ingestion_lambda_name" {
  description = "Name of the ingestion Lambda function"
  value       = aws_lambda_function.ingestion.function_name
}

output "indexing_lambda_arn" {
  description = "ARN of the indexing Lambda function"
  value       = aws_lambda_function.indexing.arn
}

output "indexing_lambda_name" {
  description = "Name of the indexing Lambda function"
  value       = aws_lambda_function.indexing.function_name
}
