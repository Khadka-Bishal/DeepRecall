"""Document conversion utilities for DeepRecall.

Extracts common document transformation logic that was duplicated
across multiple modules (pinecone_system.py, hybrid_system.py).
"""

from typing import Dict, Any
from langchain_core.documents import Document


def pinecone_match_to_document(match: Dict[str, Any]) -> Document:
    """Convert a Pinecone match response to a LangChain Document.
    
    This consolidates the repeated conversion logic that was duplicated
    4 times in pinecone_system.py.
    
    Args:
        match: A match dict from Pinecone query response containing
               'id', 'score', and 'metadata' keys.
               
    Returns:
        LangChain Document with properly formatted metadata.
    """
    metadata = match.get('metadata', {})
    
    return Document(
        page_content=metadata.get('text', ''),
        metadata={
            "chunk_id": match['id'],
            "source": metadata.get('source', 'unknown'),
            "session_id": metadata.get('session_id'), # Critical for isolation
            "page_idx": metadata.get('page_idx', 0),
            "page_number": metadata.get('page_idx', 0) + 1,
            "chunk_type": metadata.get('chunk_type', 'unknown'),
            "original_content": "{}",
            "vector_id": match['id'],
            "bbox": {
                "left": metadata.get('bbox_left', 0),
                "top": metadata.get('bbox_top', 0),
                "right": metadata.get('bbox_right', 0),
                "bottom": metadata.get('bbox_bottom', 0)
            }
        }
    )


def pinecone_match_to_scored_chunk(match: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a Pinecone match to the scored chunk format used by routes.
    
    Args:
        match: A match dict from Pinecone query response.
        
    Returns:
        Dict with 'document', 'score', 'scores', and 'retriever' keys.
    """
    return {
        "document": pinecone_match_to_document(match),
        "score": match.get('score', 0.0),
        "scores": {"pinecone": match.get('score', 0.0)},
        "retriever": "pinecone"
    }


def build_bm25_document(match: Dict[str, Any]) -> Document:
    """Convert a Pinecone match to Document for BM25 indexing.
    
    Used when building the local BM25 index from Pinecone data.
    
    Args:
        match: A match dict from Pinecone query response.
        
    Returns:
        LangChain Document suitable for BM25 retriever.
    """
    metadata = match.get('metadata', {})
    
    return Document(
        page_content=metadata.get('text', ''),
        metadata={
            "chunk_id": match['id'],
            "source": metadata.get('source', ''),
            "session_id": metadata.get('session_id'), # Critical for isolation
            "page_idx": metadata.get('page_idx', 0),
            "page_number": metadata.get('page_idx', 0) + 1,
            "chunk_type": metadata.get('chunk_type', 'unknown'),
            "bbox": {
                "left": metadata.get('bbox_left', 0),
                "top": metadata.get('bbox_top', 0),
                "right": metadata.get('bbox_right', 0),
                "bottom": metadata.get('bbox_bottom', 0)
            }
        }
    )
