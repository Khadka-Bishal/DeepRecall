
import json
import os
import boto3
import logging
from botocore.exceptions import ClientError
from openai import OpenAI
from pinecone import Pinecone

# --- Logging Configuration ---
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# --- Environment Variables ---
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "deeprecall")

if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY is missing!")
    # Fail fast during init (cold start) rather than runtime
    raise ValueError("Configuration Error: Missing OpenAI API Key")

if not PINECONE_API_KEY:
    logger.error("PINECONE_API_KEY is missing!")
    raise ValueError("Configuration Error: Missing Pinecone API Key")

# --- Global Clients (Reuse across warm invocations) ---
# This is a critical performance optimization for Lambda
s3_client = boto3.client("s3")
openai_client = OpenAI(api_key=OPENAI_API_KEY)
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)

def get_embedding(text, client):
    """Generates embedding for a single text string using OpenAI."""
    text = text.replace("\n", " ")
    response = client.embeddings.create(input=[text], model="text-embedding-3-small")
    return response.data[0].embedding


def load_chunks_from_s3(bucket, key):
    """Downloads and loads the JSON content from S3."""
    download_path = f"/tmp/{os.path.basename(key)}"
    s3_client.download_file(bucket, key, download_path)
    with open(download_path, "r") as f:
        return json.load(f)


def lambda_handler(event, context):
    """
    SQS Handler for Indexing. 
    Expects S3 Event inside SQS Message.
    Triggered when *json* files (specifically chunks) are created in the Output Bucket.
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    # Clients are now global!
    
    for record in event.get("Records", []):
        try:
            # Parse SQS Body
            body_str = record.get("body")
            if not body_str:
                logger.warning("Empty body in record")
                continue
                
            sqs_body = json.loads(body_str)
            
            # SQS can wrap S3 events. Check for "Records" inside body
            if "Records" not in sqs_body:
                # Might be a test event or different structure
                if "Event" in sqs_body and sqs_body["Event"] == "s3:TestEvent":
                     logger.info("Skipping S3 Test Event")
                     continue
                logger.warning("No S3 Records found in SQS body")
                continue

            for s3_record in sqs_body["Records"]:
                bucket_name = s3_record["s3"]["bucket"]["name"]
                key = s3_record["s3"]["object"]["key"]
                
                # We only care about the JSON file that contains chunks
                if not key.endswith(".json"):
                    logger.info(f"Skipping non-JSON file: {key}")
                    continue
                    
                logger.info(f"Processing Indexing for: {key} from bucket: {bucket_name}")
                
                # 1. Load Data
                try:
                    data = load_chunks_from_s3(bucket_name, key)
                except ClientError as e:
                    if e.response['Error']['Code'] == '404':
                         logger.error(f"File not found: {key}")
                         continue
                    raise e
                    
                
                vectors = []
                
                # Handle ADE Response Structure
                grounding = data.get("grounding", {})
                
                if "splits" in data:
                    items = data["splits"]
                elif "data" in data:
                    items = data["data"]
                else:
                    items = []

                for split_idx, item in enumerate(items):
                    markdown = item.get("markdown") or item.get("text")
                    if not markdown:
                        continue
                    
                    # Extract chunks from markdown using anchor tags
                    # Pattern: <a id='chunk-id'></a>\n\n<text content>
                    import re
                    
                    # Split by anchor tags
                    chunk_pattern = r"<a id='([^']+)'></a>"
                    parts = re.split(chunk_pattern, markdown)
                    
                    # parts will be: ['', chunk_id1, text1, chunk_id2, text2, ...]
                    # Skip first empty element, then process pairs
                    for i in range(1, len(parts), 2):
                        if i + 1 >= len(parts):
                            break
                            
                        chunk_id = parts[i]
                        chunk_text = parts[i + 1].strip()
                        
                        # Skip empty chunks
                        if not chunk_text or chunk_text == "":
                            continue
                        
                        # Get grounding data for this chunk
                        chunk_grounding = grounding.get(chunk_id, {})
                        bbox = chunk_grounding.get("box", {})
                        page_num = chunk_grounding.get("page", split_idx)
                        chunk_type = chunk_grounding.get("type", "unknown")
                        
                        # Generate embedding
                        # Note: In production, consider batching these calls if using embeddings API directly
                        # But OpenAI client handles some connection pooling.
                        embedding = get_embedding(chunk_text, openai_client)
                        
                        # Metadata with bounding box
                        metadata = {
                            "source": key,
                            "text": chunk_text[:1000],  # Pinecone has metadata size limits
                            "page_idx": page_num,
                            "chunk_type": chunk_type,
                            "bbox_left": bbox.get("left", 0),
                            "bbox_top": bbox.get("top", 0),
                            "bbox_right": bbox.get("right", 0),
                            "bbox_bottom": bbox.get("bottom", 0)
                        }
                        
                        vectors.append({
                            "id": f"{key}_{chunk_id}",
                            "values": embedding,
                            "metadata": metadata
                        })
                
                if vectors:
                    logger.info(f"Upserting {len(vectors)} vectors to Pinecone...")
                    # Pinecone client handles batching automatically for upsert? Not really, max 100 recommended usually.
                    # Since we are doing per-page, it should be fine (< 100 chunks per page).
                    index.upsert(vectors=vectors)
                    logger.info("Upsert complete.")
                else:
                    logger.warning("No text found to index.")

        except Exception as e:
            logger.error(f"Failed to process record: {e}")
            raise e # Raising triggers DLQ

