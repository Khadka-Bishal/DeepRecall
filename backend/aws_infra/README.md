# AWS Infrastructure Setup

This directory contains the scripts to deploy the DeepRecall Ingestion Pipeline to AWS.

## Prerequisites

Since you are new to the cloud, here is a checklist of what you need before running the deployment scripts:

1.  **AWS Account**: You need an active AWS account.
2.  **AWS CLI Installed & Configured**:
    - Install the AWS CLI: https://aws.amazon.com/cli/
    - Run `aws configure` in your terminal.
    - Enter your **Access Key ID**, **Secret Access Key**, **Region** (e.g., `us-east-1`), and default output format (`json`).
3.  **LandingAI API Key**:
    - You need a valid API Key from [LandingAI](https://app.landing.ai/).
    - This key will be securely passed to your Lambda function.

## Directory Structure

- `config.py`: Configuration settings (Bucket names, Region, etc.).
- `deploy_ingestion.py`: The main script that sets up S3, SQS, and Lambda.
- `lambda/ade_handler.py`: The Python code that runs inside the AWS Lambda function.

## Deployment Steps

1.  **Initialize & Install Dependencies (using uv)**:
    ```bash
    uv venv
    uv pip install boto3 "botocore[crt]" landingai-ade python-dotenv
    ```
2.  **Review Configuration**:
    - Open `.env` in the project root and fill in your `VISION_AGENT_API_KEY`.
    - (Optional) Change bucket names in `.env` if needed.
3.  **Run Deployment**:
    ```bash
    uv run backend/aws_infra/deploy_ingestion.py
    ```
    *(Using `uv run` automatically uses your virtual environment!)*.

