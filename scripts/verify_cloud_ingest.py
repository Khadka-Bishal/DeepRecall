#!/usr/bin/env python3
"""
Verify Cloud Ingestion Pipeline
-------------------------------
Simulates the frontend client to verify the backend's "Upload -> Poll" strategy.

Usage:
    python verify_cloud_ingest.py path/to/document.pdf

Prerequisites:
    pip install requests websockets asyncio aiohttp rich
"""

import sys
import os
import asyncio
import json
import logging
import requests
from pathlib import Path

# Configure
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
WS_URL = API_URL.replace("http", "ws") + "/ws"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("verifier")

async def listen_to_websocket():
    """Listen to the websocket for pipeline updates."""
    import websockets
    retry_count = 0
    max_retries = 5
    while retry_count < max_retries:
        try:
            async with websockets.connect(WS_URL) as ws:
                logger.info(f"Connected to WebSocket at {WS_URL}")
                while True:
                    message = await ws.recv()
                    data = json.loads(message)
                    if data.get("type") == "pipeline":
                        stage = data.get("stage", "UNKNOWN")
                        status = data.get("status", "unknown")
                        logger.info(f"[WebSocket] Pipeline Stage: {stage} ({status})")
                        if stage == "COMPLETE":
                            logger.info("Pipeline Complete!")
                            break
            # If we exit the context manager normally (e.g. break), we're done
            return
        except (websockets.exceptions.ConnectionClosedError, OSError) as e:
            retry_count += 1
            if retry_count >= max_retries:
                logger.error(f"WebSocket Connection Failed after {max_retries} attempts: {e}")
                return
            
            wait_time = 0.5 * retry_count
            logger.info(f"WebSocket connection failed (attempt {retry_count}/{max_retries}). Retrying in {wait_time}s...")
            await asyncio.sleep(wait_time)
        except Exception as e:
            logger.error(f"WebSocket Error: {e}")
            return

def upload_file(file_path):
    """Uploads the file to the ingest endpoint."""
    url = f"{API_URL}/ingest"
    logger.info(f"Uploading {file_path} to {url}...")
    
    with open(file_path, "rb") as f:
        files = {"file": f}
        try:
            # We set a long timeout because the backend is polling for us (sync blocking)
            response = requests.post(url, files=files, timeout=120) 
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.error("Request timed out! (Backend polling took too long)")
            sys.exit(1)
        except requests.exceptions.RequestException as e:
            logger.error(f"Upload Failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            sys.exit(1)

async def main():
    if len(sys.argv) < 2:
        print("Usage: python verify_cloud_ingest.py <path_to_pdf>")
        sys.exit(1)
        
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        sys.exit(1)

    # Start WebSocket listener in background
    ws_task = asyncio.create_task(listen_to_websocket())
    
    # Give WS a moment to connect
    await asyncio.sleep(1)
    
    # Upload File (Blocking call)
    logger.info("Starting Upload...")
    
    # We'll run upload in a separate thread so asyncio loop keeps running the WS listener
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, upload_file, file_path)
    
    logger.info("Upload & Processing Finished!")
    print("\n--- FINAL REPORT ---")
    print(json.dumps(result, indent=2))
    
    # Stop WS listener
    ws_task.cancel()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
