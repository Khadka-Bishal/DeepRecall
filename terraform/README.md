# Terraform README - Infrastructure as Code

## Overview

This directory contains Terraform configurations for managing DeepRecall's AWS infrastructure:
- S3 buckets (document storage)
- Lambda functions (document processing & indexing)
- SQS queues (async message handling)
- IAM roles (least-privilege access)

## Prerequisites

- [Terraform](https://www.terraform.io/downloads) >= 1.0
- AWS CLI configured with credentials
- Required API keys (see Configuration below)

## Quick Start

```bash
# 1. Copy example variables
cp environments/dev.tfvars.example environments/dev.tfvars

# 2. Edit dev.tfvars with your actual API keys
# IMPORTANT: dev.tfvars is gitignored - never commit secrets!

# 3. Initialize Terraform
terraform init

# 4. Preview changes
terraform plan -var-file=environments/dev.tfvars

# 5. Apply infrastructure
terraform apply -var-file=environments/dev.tfvars
```

## Configuration

### Environment Variables

Create `environments/dev.tfvars` from the example file:

```hcl
environment         = "dev"
aws_region          = "us-east-1"

# API Keys - replace with your actual keys
ade_api_key         = "your-ade-api-key"
ade_endpoint        = "https://your-endpoint.cognitiveservices.azure.com/"
openai_api_key      = "sk-proj-your-key"
pinecone_api_key    = "pcsk_your-key"
pinecone_index_name = "deeprecall-dev"
```

⚠️ **Never commit `*.tfvars` files to Git!** They contain secrets.

## Project Structure

```
terraform/
├── main.tf                     # Main configuration & modules
├── variables.tf                # Variable definitions
├── outputs.tf                  # Output values
├── .gitignore                  # Prevents committing secrets
├── modules/                    # Reusable infrastructure modules
│   ├── s3/                     # S3 bucket configurations
│   ├── lambda/                 # Lambda function deployments
│   ├── sqs/                    # SQS queue setup
│   └── iam/                    # IAM roles and policies
└── environments/
    ├── dev.tfvars.example      # Example (safe to commit)
    └── prod.tfvars.example     # Example (safe to commit)
```

## Security

- All secrets use Terraform variables (never hardcoded)
- State files (`.tfstate`) are gitignored
- Variable files (`.tfvars`) are gitignored
- Only `.tfvars.example` files are committed

## State Management

### Local State (Current)
State is stored locally in `terraform.tfstate` (gitignored for security).

### Remote State (Future - Production)
For team collaboration or production, use S3 backend:

```hcl
terraform {
  backend "s3" {
    bucket         = "deeprecall-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
```

## Common Commands

```bash
# Preview changes
terraform plan -var-file=environments/dev.tfvars

# Apply changes
terraform apply -var-file=environments/dev.tfvars

# Show current state
terraform show

# List all resources
terraform state list

# Destroy all resources (careful!)
terraform destroy -var-file=environments/dev.tfvars
```

## Migrating from Python Script

If you previously used `backend/aws_infra/deploy_ingestion.py`:

1. **Import existing resources**:
   ```bash
   terraform import aws_s3_bucket.input deeprecall-input-bishal-6336
   terraform import aws_lambda_function.ade_processor ADEDocumentProcessor
   # ... repeat for all resources
   ```

2. **Verify import**:
   ```bash
   terraform plan
   # Should show "No changes" if import was correct
   ```

3. **Future deployments** use Terraform instead of Python script

## Notes

- Terraform is declarative: define "what should exist" not "how to create"
- State tracking enables updates, rollbacks, and drift detection
- Module structure promotes reusability across environments
- Version control infrastructure alongside application code

## Resources Managed

| Resource Type | Name | Purpose |
|--------------|------|---------|
| S3 Bucket | input | Document upload storage |
| S3 Bucket | output | Processed document storage |
| Lambda | ADEDocumentProcessor | ADE document extraction |
| Lambda | ADEIndexer | Vector indexing to Pinecone |
| SQS Queue | ingestion-queue | Ingestion message queue |
| SQS Queue | indexing-queue | Indexing message queue |
| IAM Role | lambda-execution-role | Lambda permissions |

## Support

For infrastructure questions or issues, see the main project [README](../README.md).
