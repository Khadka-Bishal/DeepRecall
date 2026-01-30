import json
import os
import boto3
import logging
from urllib.parse import unquote_plus
from landingai_ade import LandingAIADE

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")

# Environment variables (set during deployment)
OUTPUT_BUCKET = os.environ.get("OUTPUT_BUCKET")
LANDINGAI_API_KEY = os.environ.get("VISION_AGENT_API_KEY")

def lambda_handler(event, context):
    """
    AWS Lambda Handler.
    Triggered by SQS Event (which wraps an S3 Event).
    """
    logger.info(f"Received event: {json.dumps(event)}")

    if not LANDINGAI_API_KEY:
        logger.error("VISION_AGENT_API_KEY is missing!")
        raise ValueError("Configuration Error: Missing LandingAI API Key")

    # Cycle through SQS Records
    for record in event.get("Records", []):
        try:
            # Parse S3 Event from SQS Body
            body = json.loads(record["body"])
            
            # Check if this is a test event or irrelevant
            if "Records" not in body:
                logger.info("Skipping non-S3 event record")
                continue
                
            for s3_record in body["Records"]:
                process_s3_record(s3_record)

        except Exception as e:
            logger.error(f"Failed to process record: {e}")
            raise e  # Raising exception triggers SQS Retry / DLQ logic

    return {"statusCode": 200, "body": "Processing Complete"}

def process_s3_record(s3_record):
    """
    Process a single S3 file upload event.
    """
    bucket_name = s3_record["s3"]["bucket"]["name"]
    key = unquote_plus(s3_record["s3"]["object"]["key"])
    
    logger.info(f"Processing object: {key} from bucket: {bucket_name}")

    if not key.lower().endswith(".pdf"):
        logger.info(f"Skipping non-PDF file: {key}")
        return

    # Check Idempotency: Have we processed this already?
    output_key_base = os.path.splitext(key)[0]
    output_md_key = f"{output_key_base}.md"
    
    try:
        s3_client.head_object(Bucket=OUTPUT_BUCKET, Key=output_md_key)
        logger.info(f"Output for {key} already exists at {output_md_key}. Skipping.")
        return
    except s3_client.exceptions.ClientError:
        # 404 means not found, so we proceed
        pass

    # Download Input File to /tmp
    download_path = f"/tmp/{os.path.basename(key)}"
    logger.info(f"Downloading to {download_path}")
    s3_client.download_file(bucket_name, key, download_path)
    
    # Layer 5: File Validation
    file_size = os.path.getsize(download_path)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    if file_size > MAX_FILE_SIZE:
        logger.error(f"File too large: {file_size} bytes")
        return
    
    # Validate PDF magic bytes
    with open(download_path, 'rb') as f:
        if not f.read(4).startswith(b'%PDF'):
            logger.error(f"Invalid PDF file: {key}")
            return
    
    logger.info(f"File validated: {file_size} bytes")

    # Call LandingAI ADE
    # Call LandingAI ADE (Using direct requests for stability)
    logger.info("Starting ADE Parse (via requests)...")
    import requests
    
    url = "https://api.va.landing.ai/v1/ade/parse"
    
    # We open the file in binary mode for upload
    with open(download_path, "rb") as f:
        files = {"document": (os.path.basename(key), f, "application/pdf")}
        data = {"model": "dpt-2-latest"}
        headers = {"Authorization": f"Bearer {LANDINGAI_API_KEY}"}
        
        try:
            resp = requests.post(url, files=files, data=data, headers=headers)
            resp.raise_for_status() # Raise error for non-200
        except requests.exceptions.RequestException as e:
            logger.error(f"ADE API Request Failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise e

    # Parse result
    result_json = resp.json()
    
    # Extract markdown (assuming standard response structure)
    # The response structure from my test is:
    # { "data": [ { "markdown": "..." } ], "version": ... }
    # Or sometimes direct depending on endpoint.
    # Looking at test output: {"data":[{"markdown":"...","chunks":...}],"splits":...}
    
    api_markdown = ""
    # The API returns a list of pages in 'data' usually
    if "data" in result_json:
        for page in result_json["data"]:
            if "markdown" in page:
                api_markdown += page["markdown"] + "\n\n"
    
    # Fallback if top-level markdown exists (unlikely in 'parse' but good for safety)
    if not api_markdown and "markdown" in result_json:
         api_markdown = result_json["markdown"]


    # Upload Results to Output Bucket
    # 1. Markdown
    s3_client.put_object(
        Bucket=OUTPUT_BUCKET,
        Key=output_md_key,
        Body=api_markdown,
        ContentType="text/markdown"
    )
    
    # 2. JSON (Raw Response)
    output_json_key = f"{output_key_base}.json"
    s3_client.put_object(
        Bucket=OUTPUT_BUCKET,
        Key=output_json_key,
        Body=json.dumps(result_json),
        ContentType="application/json"
    )
    
    logger.info(f"Successfully processed {key}. Outputs: {output_md_key}, {output_json_key}")

