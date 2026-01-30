# =============================================================================
# SQS Module - Message Queues for Document Pipeline
# =============================================================================
# Two queue pairs for the ingestion pipeline:
# 1. Ingestion Queue: Receives S3 upload notifications
# 2. Indexing Queue: Receives processed document notifications
# Each has a DLQ for failed message handling.

locals {
  # Convert days to seconds for SQS retention
  dlq_retention_seconds = var.dlq_retention_days * 24 * 60 * 60
}

# -----------------------------------------------------------------------------
# Ingestion Queue (receives S3 upload events)
# -----------------------------------------------------------------------------

resource "aws_sqs_queue" "ingestion_dlq" {
  name                      = "${var.project_name}-ingestion-dlq-${var.environment}"
  message_retention_seconds = local.dlq_retention_seconds

  tags = {
    Name    = "${var.project_name}-ingestion-dlq-${var.environment}"
    Purpose = "Dead-letter queue for failed ingestion messages"
  }
}

resource "aws_sqs_queue" "ingestion_queue" {
  name                       = "${var.project_name}-ingestion-queue-${var.environment}"
  visibility_timeout_seconds = var.visibility_timeout_seconds

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.ingestion_dlq.arn
    maxReceiveCount     = var.max_receive_count
  })

  tags = {
    Name    = "${var.project_name}-ingestion-queue-${var.environment}"
    Purpose = "Queue for document ingestion from S3 uploads"
  }
}

# -----------------------------------------------------------------------------
# Indexing Queue (receives processed document events)
# -----------------------------------------------------------------------------

resource "aws_sqs_queue" "indexing_dlq" {
  name                      = "${var.project_name}-indexing-dlq-${var.environment}"
  message_retention_seconds = local.dlq_retention_seconds

  tags = {
    Name    = "${var.project_name}-indexing-dlq-${var.environment}"
    Purpose = "Dead-letter queue for failed indexing messages"
  }
}

resource "aws_sqs_queue" "indexing_queue" {
  name                       = "${var.project_name}-indexing-queue-${var.environment}"
  visibility_timeout_seconds = var.visibility_timeout_seconds

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.indexing_dlq.arn
    maxReceiveCount     = var.max_receive_count
  })

  tags = {
    Name    = "${var.project_name}-indexing-queue-${var.environment}"
    Purpose = "Queue for vector indexing from processed documents"
  }
}

# -----------------------------------------------------------------------------
# Queue Policies - Allow S3 to send messages
# -----------------------------------------------------------------------------

resource "aws_sqs_queue_policy" "ingestion_policy" {
  queue_url = aws_sqs_queue.ingestion_queue.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowS3ToSendMessage"
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
        Action   = "sqs:SendMessage"
        Resource = aws_sqs_queue.ingestion_queue.arn
        Condition = {
          ArnLike = {
            "aws:SourceArn" = var.input_bucket_arn
          }
        }
      }
    ]
  })
}

resource "aws_sqs_queue_policy" "indexing_policy" {
  queue_url = aws_sqs_queue.indexing_queue.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowS3ToSendMessage"
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
        Action   = "sqs:SendMessage"
        Resource = aws_sqs_queue.indexing_queue.arn
        Condition = {
          ArnLike = {
            "aws:SourceArn" = var.output_bucket_arn
          }
        }
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# CloudWatch Alarms - DLQ Monitoring
# Alert if any messages end up in Dead Letter Queues (Failed Processing)
# -----------------------------------------------------------------------------

resource "aws_cloudwatch_metric_alarm" "ingestion_dlq_depth" {
  alarm_name          = "${var.project_name}-ingestion-dlq-alarm-${var.environment}"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = "60"
  statistic           = "Maximum"
  threshold           = "1"
  alarm_description   = "Alert when messages are in Ingestion DLQ (Parsing Failed)"
  treat_missing_data  = "notBreaching"

  dimensions = {
    QueueName = aws_sqs_queue.ingestion_dlq.name
  }
}

resource "aws_cloudwatch_metric_alarm" "indexing_dlq_depth" {
  alarm_name          = "${var.project_name}-indexing-dlq-alarm-${var.environment}"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = "60"
  statistic           = "Maximum"
  threshold           = "1"
  alarm_description   = "Alert when messages are in Indexing DLQ (Embedding Failed)"
  treat_missing_data  = "notBreaching"

  dimensions = {
    QueueName = aws_sqs_queue.indexing_dlq.name
  }
}
