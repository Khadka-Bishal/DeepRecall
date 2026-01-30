# DeepRecall AWS Infrastructure - Terraform Root Module

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Uncomment for production state management
  # backend "s3" {
  #   bucket         = "deeprecall-terraform-state"
  #   key            = "prod/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "deeprecall-terraform-locks"
  #   encrypt        = true
  # }
}

# -----------------------------------------------------------------------------
# Provider Configuration
# -----------------------------------------------------------------------------

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "DeepRecall"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# -----------------------------------------------------------------------------
# Variables
# -----------------------------------------------------------------------------

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "project_name" {
  description = "Project name prefix"
  type        = string
  default     = "deeprecall"
}

# Secrets (sensitive)
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
  default     = "deeprecall"
}

# Cost optimization variables
variable "lambda_memory_size" {
  description = "Lambda memory in MB (256 is cost-optimized)"
  type        = number
  default     = 256
}

variable "s3_lifecycle_days" {
  description = "Days to retain S3 objects (0 = never delete)"
  type        = number
  default     = 0  # Disabled for side project - keep files forever
}

# -----------------------------------------------------------------------------
# Modules
# -----------------------------------------------------------------------------

# S3 buckets first (no dependencies)
module "s3" {
  source = "./modules/s3"

  project_name             = var.project_name
  environment              = var.environment
  lifecycle_days_to_expire = var.s3_lifecycle_days
}

# SQS queues (depends on S3 for bucket policies)
module "sqs" {
  source = "./modules/sqs"

  project_name      = var.project_name
  environment       = var.environment
  input_bucket_arn  = module.s3.input_bucket_arn
  output_bucket_arn = module.s3.output_bucket_arn
}

# IAM role (depends on S3 and SQS for least-privilege scoping)
module "iam" {
  source = "./modules/iam"

  project_name        = var.project_name
  environment         = var.environment
  input_bucket_arn    = module.s3.input_bucket_arn
  output_bucket_arn   = module.s3.output_bucket_arn
  ingestion_queue_arn = module.sqs.ingestion_queue_arn
  indexing_queue_arn  = module.sqs.indexing_queue_arn
}

# Lambda functions (depends on IAM, S3, SQS)
module "lambda" {
  source = "./modules/lambda"

  project_name        = var.project_name
  environment         = var.environment
  memory_size         = var.lambda_memory_size
  role_arn            = module.iam.lambda_role_arn
  input_bucket_arn    = module.s3.input_bucket_arn
  output_bucket_arn   = module.s3.output_bucket_arn
  ingestion_queue_arn = module.sqs.ingestion_queue_arn
  indexing_queue_arn  = module.sqs.indexing_queue_arn

  # Secrets
  ade_api_key         = var.ade_api_key
  ade_endpoint        = var.ade_endpoint
  openai_api_key      = var.openai_api_key
  pinecone_api_key    = var.pinecone_api_key
  pinecone_index_name = var.pinecone_index_name
}

# -----------------------------------------------------------------------------
# S3 Event Triggers -> SQS
# -----------------------------------------------------------------------------

resource "aws_s3_bucket_notification" "input_trigger" {
  bucket = module.s3.input_bucket_name

  queue {
    queue_arn = module.sqs.ingestion_queue_arn
    events    = ["s3:ObjectCreated:*"]
  }

  depends_on = [module.sqs]
}

resource "aws_s3_bucket_notification" "output_trigger" {
  bucket = module.s3.output_bucket_name

  queue {
    queue_arn     = module.sqs.indexing_queue_arn
    events        = ["s3:ObjectCreated:*"]
    filter_suffix = ".json"
  }

  depends_on = [module.sqs]
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------

output "input_bucket" {
  description = "S3 bucket for document uploads"
  value       = module.s3.input_bucket_name
}

output "output_bucket" {
  description = "S3 bucket for processed documents"
  value       = module.s3.output_bucket_name
}

output "ingestion_lambda_arn" {
  description = "ARN of the document processing Lambda"
  value       = module.lambda.ingestion_lambda_arn
}

output "indexing_lambda_arn" {
  description = "ARN of the indexing Lambda"
  value       = module.lambda.indexing_lambda_arn
}
