# IAM Module - Lambda Execution Role

# -----------------------------------------------------------------------------
# Lambda Execution Role
# -----------------------------------------------------------------------------

resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-lambda-role-${var.environment}"
  }
}

# -----------------------------------------------------------------------------
# CloudWatch Logs (required for Lambda logging)
# -----------------------------------------------------------------------------

resource "aws_iam_role_policy_attachment" "basic_execution" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# -----------------------------------------------------------------------------
# S3 Access - Scoped to specific buckets (LEAST PRIVILEGE)
# -----------------------------------------------------------------------------

resource "aws_iam_role_policy" "lambda_s3" {
  name = "${var.project_name}-lambda-s3-${var.environment}"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3ObjectAccess"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          "${var.input_bucket_arn}/*",
          "${var.output_bucket_arn}/*"
        ]
      },
      {
        Sid    = "S3BucketList"
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = [
          var.input_bucket_arn,
          var.output_bucket_arn
        ]
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# SQS Access - Scoped to specific queues (LEAST PRIVILEGE)
# -----------------------------------------------------------------------------

resource "aws_iam_role_policy" "lambda_sqs" {
  name = "${var.project_name}-lambda-sqs-${var.environment}"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "SQSReceiveMessages"
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = [
          var.ingestion_queue_arn,
          var.indexing_queue_arn
        ]
      }
    ]
  })
}
