from typing import List, Dict, Any
from langchain_core.documents import Document
from core.utils import pinecone_match_to_document

def rrf_fusion(
    bm25_docs: List[Document],
    vector_results: List[Dict],
    k: int = 60
) -> List[Dict[str, Any]]:
    """Apply Reciprocal Rank Fusion to combine BM25 and vector results.
    
    Args:
        bm25_docs: Documents retrieved from BM25.
        vector_results: Match dictionaries from Pinecone vector search.
        k: RRF constant (default 60).
        
    Returns:
        List of fused results sorted by RRF score.
    """
    rrf_scores: Dict[str, float] = {}
    doc_map: Dict[str, Document] = {}
    raw_scores: Dict[str, Dict[str, float]] = {}
    
    # Process BM25 results
    for rank, doc in enumerate(bm25_docs):
        doc_id = doc.metadata.get("chunk_id")
        if doc_id not in rrf_scores:
            rrf_scores[doc_id] = 0.0
            doc_map[doc_id] = doc
            raw_scores[doc_id] = {"bm25": 0.0, "pinecone": 0.0}
        
        score = 1.0 / (k + rank + 1)
        rrf_scores[doc_id] += score
        raw_scores[doc_id]["bm25"] = 1.0 - (rank / max(len(bm25_docs), 1))
    
    # Process vector results
    for rank, result in enumerate(vector_results):
        doc_id = result['id']
        if doc_id not in rrf_scores:
            doc = pinecone_match_to_document(result)
            rrf_scores[doc_id] = 0.0
            doc_map[doc_id] = doc
            raw_scores[doc_id] = {"bm25": 0.0, "pinecone": 0.0}
        
        score = 1.0 / (k + rank + 1)
        rrf_scores[doc_id] += score
        raw_scores[doc_id]["pinecone"] = result.get('score', 0.0)
    
    # Sort by RRF score
    sorted_ids = sorted(rrf_scores, key=rrf_scores.get, reverse=True)
    
    return [
        {
            "document": doc_map[doc_id],
            "score": float(rrf_scores[doc_id]),
            "scores": {k: float(v) for k, v in raw_scores[doc_id].items()}
        }
        for doc_id in sorted_ids
    ]
