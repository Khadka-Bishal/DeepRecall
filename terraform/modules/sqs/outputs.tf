# =============================================================================
# SQS Module Outputs
# =============================================================================

output "ingestion_queue_url" {
  description = "URL of the ingestion SQS queue"
  value       = aws_sqs_queue.ingestion_queue.url
}

output "ingestion_queue_arn" {
  description = "ARN of the ingestion SQS queue"
  value       = aws_sqs_queue.ingestion_queue.arn
}

output "indexing_queue_url" {
  description = "URL of the indexing SQS queue"
  value       = aws_sqs_queue.indexing_queue.url
}

output "indexing_queue_arn" {
  description = "ARN of the indexing SQS queue"
  value       = aws_sqs_queue.indexing_queue.arn
}

output "ingestion_dlq_arn" {
  description = "ARN of the ingestion dead-letter queue"
  value       = aws_sqs_queue.ingestion_dlq.arn
}

output "indexing_dlq_arn" {
  description = "ARN of the indexing dead-letter queue"
  value       = aws_sqs_queue.indexing_dlq.arn
}
