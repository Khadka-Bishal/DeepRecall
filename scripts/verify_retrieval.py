import requests
import json
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

API_URL = "http://127.0.0.1:8001"
CHAT_ENDPOINT = f"{API_URL}/chat"

def verify_retrieval():
    logger.info("Starting Retrieval Verification...")
    
    # 1. Define a query relevant to our test document (test1.pdf containing balance sheet)
    query = "What are the total assets?"
    
    payload = {
        "query": query,
        "history": [],
        "overrides": {}
    }
    
    try:
        logger.info(f"Sending query: '{query}' to {CHAT_ENDPOINT}...")
        response = requests.post(CHAT_ENDPOINT, json=payload)
        
        if response.status_code != 200:
            logger.error(f"Chat request failed with status {response.status_code}: {response.text}")
            return False
            
        data = response.json()
        
        # 2. Inspect Answer present
        answer = data.get("content", "")
        logger.info(f"LLM Answer: {answer[:100]}...")
        
        # 3. Inspect Retrieved Chunks for Bounding Boxes
        chunks = data.get("retrievedChunks", [])
        logger.info(f"Retrieved {len(chunks)} chunks.")
        
        bbox_found = False
        for i, chunk in enumerate(chunks):
            chunk_id = chunk.get("id")
            bbox = chunk.get("bbox")
            content = chunk.get("content", "")[:50]
            
            log_msg = f"Chunk {i+1} [ID: {chunk_id}]: {content}..."
            if bbox:
                log_msg += f" | BBOX: {bbox}"
                bbox_found = True
            else:
                log_msg += " | BBOX: None"
            
            logger.info(log_msg)
            
        if bbox_found:
            logger.info("✅ SUCCESS: Bounding boxes found in retrieval results!")
            return True
        else:
            logger.warning("⚠️  WARNING: No bounding boxes found in chunks. Ensure document was ingested with bbox logic.")
            return False

    except requests.exceptions.ConnectionError:
        logger.error(f"Could not connect to server at {API_URL}. Is it running?")
        return False
    except Exception as e:
        logger.exception(f"An error occurred: {e}")
        return False

if __name__ == "__main__":
    success = verify_retrieval()
    sys.exit(0 if success else 1)
