# =============================================================================
# IAM Module Variables
# =============================================================================

variable "project_name" {
  description = "Project name prefix for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

# Bucket ARNs for least-privilege S3 access
variable "input_bucket_arn" {
  description = "ARN of the input S3 bucket"
  type        = string
}

variable "output_bucket_arn" {
  description = "ARN of the output S3 bucket"
  type        = string
}

# Queue ARNs for least-privilege SQS access
variable "ingestion_queue_arn" {
  description = "ARN of the ingestion SQS queue"
  type        = string
}

variable "indexing_queue_arn" {
  description = "ARN of the indexing SQS queue"
  type        = string
}
