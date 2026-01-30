# =============================================================================
# Lambda Module - Document Processing Functions
# =============================================================================
# Two Lambda functions for the ingestion pipeline:
# 1. Ingestion: Parse documents using Azure Document Intelligence
# 2. Indexing: Embed and store in Pinecone vector database

locals {
  # Extract bucket name from ARN (format: arn:aws:s3:::bucket-name)
  output_bucket_name = split(":", var.output_bucket_arn)[5]
}

# -----------------------------------------------------------------------------
# Ingestion Lambda (ADE Parser)
# Triggered by: SQS (from S3 upload events)
# -----------------------------------------------------------------------------

resource "aws_lambda_function" "ingestion" {
  function_name = "${var.project_name}-ingestion-${var.environment}"
  role          = var.role_arn
  handler       = "lambda_function.lambda_handler"
  runtime       = var.runtime
  timeout       = var.timeout
  memory_size   = var.memory_size
  architectures = ["x86_64"]  # Keep x86 for compatibility with pre-built packages

  # Deployment package
  filename         = "${path.module}/${var.lambda_package_path}/ingestion_package.zip"
  source_code_hash = filebase64sha256("${path.module}/${var.lambda_package_path}/ingestion_package.zip")

  environment {
    variables = {
      VISION_AGENT_API_KEY = var.ade_api_key
      OUTPUT_BUCKET        = local.output_bucket_name
      OPENAI_API_KEY       = "placeholder"  # Not used by ingestion
    }
  }

  tags = {
    Name    = "${var.project_name}-ingestion-${var.environment}"
    Purpose = "Document parsing with Azure Document Intelligence"
  }
}

# SQS trigger for ingestion
resource "aws_lambda_event_source_mapping" "ingestion_trigger" {
  event_source_arn = var.ingestion_queue_arn
  function_name    = aws_lambda_function.ingestion.arn
  batch_size       = 1
  enabled          = true
}

# -----------------------------------------------------------------------------
# Indexing Lambda (Embed -> Pinecone)
# Triggered by: SQS (from processed document events)
# -----------------------------------------------------------------------------

resource "aws_lambda_function" "indexing" {
  function_name = "${var.project_name}-indexing-${var.environment}"
  role          = var.role_arn
  handler       = "lambda_function.lambda_handler"
  runtime       = var.runtime
  timeout       = var.timeout
  memory_size   = var.memory_size
  architectures = ["x86_64"]  # Keep x86 for compatibility

  # Deployment package
  filename         = "${path.module}/${var.lambda_package_path}/indexing_package.zip"
  source_code_hash = filebase64sha256("${path.module}/${var.lambda_package_path}/indexing_package.zip")

  environment {
    variables = {
      OPENAI_API_KEY      = var.openai_api_key
      PINECONE_API_KEY    = var.pinecone_api_key
      PINECONE_INDEX_NAME = var.pinecone_index_name
    }
  }

  tags = {
    Name    = "${var.project_name}-indexing-${var.environment}"
    Purpose = "Vector embedding and Pinecone indexing"
  }
}

# SQS trigger for indexing
resource "aws_lambda_event_source_mapping" "indexing_trigger" {
  event_source_arn = var.indexing_queue_arn
  function_name    = aws_lambda_function.indexing.arn
  batch_size       = 1
  enabled          = true
}

# -----------------------------------------------------------------------------
# CloudWatch Log Groups
# Explicitly managed to enforce retention policies
# -----------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "ingestion_logs" {
  name              = "/aws/lambda/${aws_lambda_function.ingestion.function_name}"
  retention_in_days = 14

  tags = {
    Name        = "/aws/lambda/${aws_lambda_function.ingestion.function_name}"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "indexing_logs" {
  name              = "/aws/lambda/${aws_lambda_function.indexing.function_name}"
  retention_in_days = 14

  tags = {
    Name        = "/aws/lambda/${aws_lambda_function.indexing.function_name}"
    Environment = var.environment
  }
}
