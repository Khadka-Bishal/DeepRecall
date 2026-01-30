# =============================================================================
# Lambda Module Variables
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

variable "role_arn" {
  description = "IAM Role ARN for Lambda execution"
  type        = string
}

# -----------------------------------------------------------------------------
# Resource ARNs
# -----------------------------------------------------------------------------

variable "input_bucket_arn" {
  description = "ARN of the input S3 bucket"
  type        = string
}

variable "output_bucket_arn" {
  description = "ARN of the output S3 bucket"
  type        = string
}

variable "ingestion_queue_arn" {
  description = "ARN of the ingestion SQS queue"
  type        = string
}

variable "indexing_queue_arn" {
  description = "ARN of the indexing SQS queue"
  type        = string
}

# -----------------------------------------------------------------------------
# Lambda Configuration
# -----------------------------------------------------------------------------

variable "runtime" {
  description = "Python runtime version"
  type        = string
  default     = "python3.11"
}

variable "memory_size" {
  description = "Lambda memory in MB (CPU scales with memory)"
  type        = number
  default     = 256  # Cost-optimized default
}

variable "timeout" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 300
}

variable "lambda_package_path" {
  description = "Base path to Lambda deployment packages"
  type        = string
  default     = "../../../backend/aws_infra"
}

# -----------------------------------------------------------------------------
# Secrets (marked sensitive)
# -----------------------------------------------------------------------------

variable "ade_api_key" {
  description = "Azure Document Intelligence API key"
  type        = string
  sensitive   = true
}

variable "ade_endpoint" {
  description = "Azure Document Intelligence endpoint"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
}

variable "pinecone_api_key" {
  description = "Pinecone API key"
  type        = string
  sensitive   = true
}

variable "pinecone_index_name" {
  description = "Pinecone index name"
  type        = string
}
