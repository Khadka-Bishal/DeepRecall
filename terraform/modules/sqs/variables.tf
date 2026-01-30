# =============================================================================
# SQS Module Variables
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

variable "input_bucket_arn" {
  description = "ARN of the input S3 bucket (for queue policy)"
  type        = string
}

variable "output_bucket_arn" {
  description = "ARN of the output S3 bucket (for queue policy)"
  type        = string
}

variable "visibility_timeout_seconds" {
  description = "SQS visibility timeout (should be >= Lambda timeout)"
  type        = number
  default     = 300
}

variable "max_receive_count" {
  description = "Max retries before sending to DLQ"
  type        = number
  default     = 3
}

variable "dlq_retention_days" {
  description = "Days to retain messages in DLQ (cost optimization)"
  type        = number
  default     = 4  # Reduced from 14 days to save costs
}
