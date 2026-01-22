"""Cross-encoder re-ranker for final relevance scoring."""

from time import perf_counter
from typing import List, Dict, Any
from sentence_transformers import CrossEncoder


class CrossEncoderReranker:
    """Re-rank retrieved documents using a cross-encoder model."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Initialize the cross-encoder re-ranker.

        Args:
            model_name: HuggingFace cross-encoder model name
        """
        self.model = CrossEncoder(model_name)
        print(f"[reranker] loaded {model_name}")

    def rerank(
        self, query: str, documents: List[Dict[str, Any]], top_k: int = None
    ) -> List[Dict[str, Any]]:
        """
        Re-rank documents using cross-encoder scores.

        Args:
            query: The search query
            documents: List of document dicts with 'document', 'score', 'scores' keys
            top_k: Number of top results to return (if None, returns all)

        Returns:
            Re-ranked list of documents with updated scores
        """
        if not documents:
            return documents

        t0 = perf_counter()

        pairs = [[query, doc["document"].page_content] for doc in documents]

        ce_scores = self.model.predict(pairs)

        reranked_docs = []
        for doc, ce_score in zip(documents, ce_scores):
            reranked_doc = doc.copy()
            reranked_doc["scores"]["cross_encoder"] = float(ce_score)
            reranked_doc["score"] = float(ce_score)
            reranked_docs.append(reranked_doc)

        reranked_docs.sort(key=lambda x: x["score"], reverse=True)

        if top_k is not None:
            reranked_docs = reranked_docs[:top_k]

        elapsed_ms = (perf_counter() - t0) * 1000
        print(
            f"[rerank] {len(documents)}→{len(reranked_docs)} docs ({elapsed_ms:.0f}ms)"
        )

        return reranked_docs
