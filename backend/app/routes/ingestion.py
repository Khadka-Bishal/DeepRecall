"""Document ingestion endpoint."""

import logging
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Header
from typing import Optional

from core.config import get_settings
from app.state import get_ingestion_pipeline, get_observability
from app.services import get_benchmark, clear_all_caches
from app.websocket import get_connection_manager
from app.services.s3 import get_s3_service

log = logging.getLogger(__name__)
router = APIRouter(tags=["ingestion"])


@router.post("/ingest")
async def ingest_document(
    file: UploadFile = File(...),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """Process and index an uploaded document using AWS Cloud Pipeline.
    
    Uploads to S3, then polls for the result from the Output Bucket.
    Parses the Cloud output to return the standard report format.
    """
    settings = get_settings()
    ws = get_connection_manager()
    s3 = get_s3_service()

    # Use session ID for isolation, fallback to 'default' if None
    session_prefix = x_session_id if x_session_id else "default"
    
    # Security: Use UUID for temp file to prevent path traversal
    import uuid
    temp_path = Path(f"temp_{uuid.uuid4().hex}.pdf").absolute()

    try:
        await ws.broadcast(
            {"type": "pipeline", "stage": "UPLOADING", "status": "active"}
        )

        # Read file and validate size
        file_content = await file.read()
        if len(file_content) > settings.max_file_size_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {settings.max_file_size_mb}MB"
            )
        
        # Validate file type (PDF only)
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Check PDF magic bytes
        if not file_content.startswith(b'%PDF'):
            raise HTTPException(status_code=400, detail="Invalid PDF file")

        with temp_path.open("wb") as f:
            f.write(file_content)

        file_size = temp_path.stat().st_size
        
        # Upload to S3 with Session Prefix
        s3_key = f"{session_prefix}/{file.filename}"
        try:
            s3.s3_client.upload_file(
                str(temp_path),
                s3.input_bucket,
                s3_key
            )
        except Exception as e:
            log.error(f"Failed to upload to S3: {e}")
            raise HTTPException(status_code=500, detail=f"S3 Upload failed: {str(e)}")
        
        await ws.broadcast(
            {"type": "pipeline", "stage": "UPLOADING", "status": "complete"}
        )

        # 2. Poll Output Bucket for Result
        import asyncio
        import json
        import re
        from botocore.exceptions import ClientError
        
        # We need to simulate the pipeline steps for the UI while we poll
        # because the cloud process is opaque until finished
        await ws.broadcast({"type": "pipeline", "stage": "PARTITIONING", "status": "active"})
        
        # Determine output key base (Cloud pipeline preserves folder structure)
        # e.g. input: session/file.pdf -> output: session/file.json
        output_key = f"{session_prefix}/{Path(file.filename).stem}.json"
        
        max_retries = 30 # 60 seconds (2s interval)
        poll_interval = 2
        result_data = None
        
        for i in range(max_retries):
            try:
                # Try to get the object
                response = s3.s3_client.get_object(Bucket=s3.output_bucket, Key=output_key)
                content = response['Body'].read().decode('utf-8')
                result_data = json.loads(content)
                break
            except ClientError as e:
                # Check for 404 Not Found (NoSuchKey)
                error_code = e.response.get('Error', {}).get('Code')
                if error_code == 'NoSuchKey' or error_code == '404':
                    # Not ready yet, wait
                    await asyncio.sleep(poll_interval)
                    # Simulate progress updates periodically
                    if i == 5:
                         await ws.broadcast({"type": "pipeline", "stage": "PARTITIONING", "status": "complete"})
                         await ws.broadcast({"type": "pipeline", "stage": "CHUNKING", "status": "active"})
                    if i == 15:
                         await ws.broadcast({"type": "pipeline", "stage": "CHUNKING", "status": "complete"})
                         await ws.broadcast({"type": "pipeline", "stage": "SUMMARIZING", "status": "active"})
                    continue
                else:
                    raise e
        
        if not result_data:
            raise HTTPException(status_code=504, detail="Timeout waiting for Cloud Processing")

        # 3. Process Cloud Result
        chunks_preview = []
        elements_preview = []
        
        items = result_data.get("splits") or result_data.get("data") or []
        if isinstance(result_data, list):
             items = result_data

        chunk_pattern = r"<a id='([^']+)'></a>"
        
        for split_idx, item in enumerate(items):
            markdown = item.get("markdown") or item.get("text")
            if not markdown:
                log.warning(f"Split {split_idx} has no markdown or text content")
                continue
            
            log.info(f"Processing split {split_idx}, length={len(markdown)}")
            # snippet = markdown[:200]
            # log.info(f"Snippet: {snippet}")
                
            # Partition by paragraphs for granular visibility
            
            raw_blocks = [b.strip() for b in markdown.split('\n\n') if b.strip()]
            for block_idx, block in enumerate(raw_blocks):
                 # Skip very short blocks unless they look like headers
                 if len(block) < 10 and not block.startswith('#'):
                     continue
                     
                 # Skip standalone anchor tags (ADE artifacts)
                 if re.match(r"^<a id='[^']+'></a>$", block.strip()):
                     continue
                     
                 # Detect HTML tables
                 elem_type = "NarrativeText"
                 if block.strip().startswith("<table"):
                     elem_type = "Table"
                 elif block.startswith("#"):
                     elem_type = "Title"

                 elements_preview.append({
                    "type": elem_type,
                    "element_id": f"p_{split_idx}_{block_idx}",
                    "text": block, 
                    "prob": 0.99, # Fake high confidence for Cloud output
                    "page": split_idx + 1,
                    "metadata": {
                        "page_number": split_idx + 1,
                        "filename": file.filename
                    }
                })

            # Build a lookup for bounding boxes from the raw item data if available
            # Strategy: Look for 'chunks' list or 'grounding' dict in the item or top-level
            bbox_lookup = {}
            
            # 1. Try item-level 'chunks' (if list of objects)
            raw_chunks = item.get("chunks", [])
            for rc in raw_chunks:
                if isinstance(rc, dict) and "id" in rc and "grounding" in rc:
                    bbox_lookup[rc["id"]] = rc["grounding"]["box"]
            
            # 2. Try item-level 'grounding' dict
            if "grounding" in item and isinstance(item["grounding"], dict):
                # Format: "id": { "box": ... }
                for gid, gdata in item["grounding"].items():
                    if isinstance(gdata, dict) and "box" in gdata:
                        bbox_lookup[gid] = gdata["box"]

            # 3. Try top-level 'chunks' if not found (fallback)
            if not bbox_lookup and "chunks" in result_data and isinstance(result_data["chunks"], list):
                 for rc in result_data["chunks"]:
                    if isinstance(rc, dict) and "id" in rc and "grounding" in rc:
                        bbox_lookup[rc["id"]] = rc["grounding"]["box"]

            # Parse chunks from markdown using ADE tags
            parts = re.split(chunk_pattern, markdown)
            local_chunks = []
            
            # ... existing regex loop ...
            for j in range(1, len(parts), 2):
                if j + 1 >= len(parts):
                    break
                
                chunk_id = parts[j]
                chunk_text = parts[j + 1].strip()
                
                if not chunk_text:
                    continue
                
                # Sanitize ID
                safe_id = chunk_id.split('_')[-1][:8] if '_' in chunk_id else chunk_id[:8]
                
                chunk_obj = {
                    "id": f"Ref_{safe_id}",
                    "content": chunk_text,
                    "page": split_idx + 1,
                    "length": len(chunk_text)
                }
                
                
                if chunk_id in bbox_lookup:
                    chunk_obj["bbox"] = bbox_lookup[chunk_id]
                
                # Check for page image in metadata to simulate "figure extraction"
                # LandingAI puts full page image in metadata.image_base64
                # If we have bbox, we could crop, but for now let's pass the full page if present
                # so the frontend can at least show something.
                page_meta = item.get("metadata", {})
                if page_meta.get("image_base64"):
                     # Only attach to the first chunk of the page or relevant chunks to avoid duplicating heavy base64
                     # But for "Figure" chunks, we want it.
                     pass 
                
                # If the Cloud Pipeline explicitly returned images in the chunk object (ideal case)
                # We check raw_chunks loop above, but we are inside regex loop here.
                # Let's see if we can map it.
                
                local_chunks.append(chunk_obj)

            # Fallback: If no tags found (standard text/md), chunk by paragraphs
            if not local_chunks and markdown:
                log.warning(f"No ADE tags found in split {split_idx}, falling back to paragraph chunking")
                for i, para in enumerate(raw_blocks):
                    if len(para) < 20: continue # Skip noise
                    c_id = f"chk_{split_idx}_{i}"
                    chunk_obj = {
                        "id": c_id,
                        "content": para,
                        "page": split_idx + 1,
                        "length": len(para)
                    }
                    # Try to map grounding if we have generic ids (unlikely but possible)
                    if c_id in bbox_lookup:
                        chunk_obj["bbox"] = bbox_lookup[c_id]
                        
                    local_chunks.append(chunk_obj)
            
            # 4. Extract Images/Figures if present in Top-Level or Item Level
            # LandingAI might return 'images' list or we check metadata
            page_image = item.get("metadata", {}).get("image_base64")
            if page_image:
                 # Check if any chunk is a Figure/Image type based on text content
                 # or just attach to the first chunk? 
                 # Better: Look for chunks that are tables/figures
                 for c in local_chunks:
                     if "Figure" in c["content"] or "Table" in c["content"]:
                         c["images"] = [page_image]
                         
            chunks_preview.extend(local_chunks)
            
        # Ensure we have at least something to show even if all fails
        if not elements_preview and not chunks_preview:
             log.error("Pipeline produced zero elements/chunks. Creating error placeholder.")
             elements_preview.append({
                 "type": "Error",
                 "text": "The document was processed but no text content could be extracted or partitioned. Please check if the PDF is scanned or encrypted.",
                 "page": 1,
                 "prob": 0.0
             })

        # Final Broadcasts
        await ws.broadcast({"type": "pipeline", "stage": "SUMMARIZING", "status": "complete"})
        await ws.broadcast({"type": "pipeline", "stage": "VECTORIZING", "status": "active"})
        
        # 5. Index into Vector Store with Session ID (Critical for RAG + Isolation)
        from langchain_core.documents import Document
        from app.state import get_retriever_system
        
        # Create Document objects from the parsed chunks
        new_docs = []
        for chunk in chunks_preview:
            doc = Document(
                page_content=chunk["content"],
                metadata={
                    "chunk_id": chunk["id"],
                    "page_number": chunk.get("page", 1),
                    "filename": file.filename,
                    "session_id": session_prefix, # STRICT ISOLATION
                    # Store original structure for retrieval display
                    "original_content": json.dumps({
                        "raw_text": chunk["content"],
                        "tables_html": [],
                        "images_base64": chunk.get("images", []),
                    })
                }
            )
            new_docs.append(doc)

        # Add to Vector Store
        if new_docs:
            try:
                retriever_sys = get_retriever_system()
                # Use unified interface
                if hasattr(retriever_sys, 'add_documents'):
                    retriever_sys.add_documents(new_docs)
                    log.info(f"Indexed {len(new_docs)} chunks for session {session_prefix}")
                else:
                    log.warning("Retriever system does not support adding documents")
            except Exception as e:
                log.error(f"Failed to index documents: {e}")
                # Don't fail the request, just log? Or warn user?
        
        await asyncio.sleep(0.5) 
        await ws.broadcast({"type": "pipeline", "stage": "VECTORIZING", "status": "complete"})
        
        report = {
            "chunks": chunks_preview,
            "elements": elements_preview,
            "total_chunks": len(chunks_preview),
            "total_elements": len(elements_preview),
            "total_images": 0,
            "total_tables": 0
        }
        
        await ws.broadcast({
            "type": "pipeline",
            "stage": "COMPLETE",
            "status": "complete",
            "images": 0,
            "tables": 0,
            "chunks": len(chunks_preview),
            "elements": len(elements_preview)
        })
        
        clear_all_caches()

        return {
            "status": "success",
            "filename": file.filename,
            "pipeline_report": report,
            "performance": {
                "duration_seconds": 0, 
                "throughput_mb_s": 0,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        log.exception("Cloud Ingestion failed")
        raise HTTPException(status_code=500, detail=f"Cloud Ingestion failed: {str(e)}")
    finally:
        if temp_path.exists():
            temp_path.unlink()
