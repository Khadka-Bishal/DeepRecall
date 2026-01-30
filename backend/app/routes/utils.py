"""Shared utilities for route handlers."""

import json
from typing import Dict, Any


def format_chunk_response(item: Dict[str, Any]) -> Dict[str, Any]:
    """Format a retrieval result into API response chunk format.
    
    Args:
        item: A dict containing 'document', 'score', and 'scores' keys
              from the retrieval system.
              
    Returns:
        Formatted chunk dict for API response.
    """
    doc = item["document"]
    
    # Parse original content metadata
    try:
        orig = json.loads(doc.metadata.get("original_content", "{}"))
    except json.JSONDecodeError:
        orig = {}
    
    raw_id = doc.metadata.get("chunk_id", "unknown")
    # Sanitize ID for frontend display (hide S3 paths)
    sanitized = raw_id.split('_')[-1][:8] if '_' in raw_id else raw_id[:8]
    
    return {
        "id": f"Ref_{sanitized}",
        "content": orig.get("raw_text", doc.page_content),
        "images": orig.get("images_base64", []),
        "score": item.get("score", 0.0),
        "scores": item.get("scores", {"bm25": 0.0, "vector": 0.0}),
        "page": doc.metadata.get("page_number", 1),
        "chunkType": doc.metadata.get("chunk_type", "unknown"),
        "bbox": doc.metadata.get("bbox", {}),
    }


def format_chunks_response(items: list) -> list:
    """Format multiple retrieval results.
    
    Args:
        items: List of retrieval result dicts.
        
    Returns:
        List of formatted chunk dicts.
    """
    return [format_chunk_response(item) for item in items]
