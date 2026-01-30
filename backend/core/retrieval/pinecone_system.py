"""Pinecone-based retrieval system for serverless vector search."""

import logging
import uuid
import asyncio
from typing import List, Dict, Any, Tuple, AsyncIterator

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever
from pinecone import Pinecone

from core.config import get_settings
from core.utils import pinecone_match_to_document, pinecone_match_to_scored_chunk
from .answer_generator import AnswerGenerator
from .fusion import rrf_fusion
try:
    from .cross_encoder_reranker import CrossEncoderReranker
except ImportError:
    CrossEncoderReranker = None

from .query_expander import MultiQueryExpander

log = logging.getLogger(__name__)


class PineconeRetrieverSystem:
    """Retrieval system using Pinecone for semantic search.
    
    Integrates with the serverless AWS Lambda indexing pipeline.
    Supports hybrid BM25 + vector search with optional reranking.
    """
    
    def __init__(
        self, 
        index_name: str = None,
        top_k: int = None,
        enable_hybrid: bool = None,
        enable_reranker: bool = None,
        rerank_top_n: int = None
    ):
        """Initialize the Pinecone retriever system.
        
        Args:
            index_name: Pinecone index name. Defaults to settings.
            top_k: Number of results to return. Defaults to settings.
            enable_hybrid: Whether to enable BM25 hybrid search.
            enable_reranker: Whether to enable cross-encoder reranking.
            rerank_top_n: Number of results to consider for reranking.
        """
        settings = get_settings()
        
        self.index_name = index_name or settings.pinecone_index_name
        self.top_k = top_k or settings.retrieval_top_k
        self.enable_hybrid = enable_hybrid if enable_hybrid is not None else settings.enable_hybrid_search
        self.enable_reranker = enable_reranker if enable_reranker is not None else settings.enable_reranker
        self.rerank_top_n = rerank_top_n or settings.rerank_top_n
        
        # Initialize clients
        self.embedding_model = OpenAIEmbeddings(model=settings.embedding_model)
        self.llm = ChatOpenAI(model=settings.llm_model, temperature=settings.llm_temperature)
        self.answer_generator = AnswerGenerator(llm=self.llm)
        self.multi_query_expander = MultiQueryExpander(llm=self.llm, num_queries=settings.num_query_expansions)
        
        # Initialize Pinecone
        if not settings.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY not found in environment variables")
        
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.index = self.pc.Index(self.index_name)
        
        # BM25 index (only if hybrid enabled - lazy loaded)
        self.bm25_retriever = None
        self.documents_cache: List[Document] = []
        self._bm25_build_attempted = False
        
        # Initialize reranker if enabled
        if self.enable_reranker and CrossEncoderReranker:
            self.cross_encoder_reranker = CrossEncoderReranker()
        else:
            if self.enable_reranker:
                log.warning("Reranking disabled: 'sentence-transformers' not installed.")
            self.enable_reranker = False
            self.cross_encoder_reranker = None
        
        log.info("Connected to Pinecone index: %s", self.index_name)
        if self.enable_hybrid:
            log.warning("Hybrid search enabled (not recommended for production)")
        else:
            log.info("Vector search only (production mode)")
        if self.enable_reranker:
            log.info("Reranking enabled (top-%d → top-%d)", self.rerank_top_n, self.top_k)

    def initialize_vector_store(self, documents: List[Document]) -> Any:
        """Upsert documents to Pinecone.
        
        Args:
            documents: List of LangChain Documents to index.
            
        Returns:
            The Pinecone index instance.
        """
        log.info("Indexing %d documents to Pinecone...", len(documents))
        
        vectors = []
        for doc in documents:
            vec_id = doc.metadata.get("chunk_id") or f"chunk_{uuid.uuid4()}"
            embedding = self._get_embedding(doc.page_content)
            
            metadata = {
                "text": doc.page_content,
                "source": doc.metadata.get("source", "local_upload"),
                "session_id": doc.metadata.get("session_id"), # Critical for isolation
                "page_idx": doc.metadata.get("page_idx") or doc.metadata.get("page_number", 1) - 1,
                "chunk_type": doc.metadata.get("chunk_type", "text"),
                "bbox_left": doc.metadata.get("bbox", {}).get("left", 0),
                "bbox_top": doc.metadata.get("bbox", {}).get("top", 0),
                "bbox_right": doc.metadata.get("bbox", {}).get("right", 0),
                "bbox_bottom": doc.metadata.get("bbox", {}).get("bottom", 0),
            }
            
            vectors.append({
                "id": vec_id,
                "values": embedding,
                "metadata": metadata
            })

        # Batch upsert
        BATCH_SIZE = 100
        for i in range(0, len(vectors), BATCH_SIZE):
            batch = vectors[i:i + BATCH_SIZE]
            self.index.upsert(vectors=batch)
            
        log.info("Successfully indexed %d vectors", len(documents))
        return self.index
    
    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding for a query string."""
        return self.embedding_model.embed_query(text)
    
    def _build_bm25_index(self, max_docs: int = 50) -> None:
        """Build BM25 index from documents in Pinecone.
        
        WARNING: Not recommended for production with large datasets.
        """
        if self.bm25_retriever is not None or self._bm25_build_attempted:
            return
        
        self._bm25_build_attempted = True
        log.info("Building BM25 index (max %d docs)...", max_docs)
        
        settings = get_settings()
        stats = self.index.describe_index_stats()
        total_vectors = stats['total_vector_count']
        
        if total_vectors > max_docs:
            log.warning("Index has %d vectors, limiting BM25 to %d", total_vectors, max_docs)
        
        # Query with dummy vector to get documents
        dummy_embedding = [0.0] * settings.embedding_dimension
        
        results = self.index.query(
            vector=dummy_embedding,
            top_k=min(max_docs, total_vectors),
            include_metadata=True
        )
        
        all_docs = [pinecone_match_to_document(match) for match in results['matches']]
        
        if not all_docs:
            log.warning("No documents found for BM25 index")
            return
        
        self.documents_cache = all_docs
        self.bm25_retriever = BM25Retriever.from_documents(all_docs)
        self.bm25_retriever.k = self.top_k
        
        log.info("BM25 index built with %d documents", len(all_docs))
    

    
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the index and local cache."""
        self.initialize_vector_store(documents)
        
        # Update local cache and BM25 if already built
        if self.documents_cache is not None:
            self.documents_cache.extend(documents)
            
        if self.bm25_retriever is not None:
            self.bm25_retriever.add_documents(documents)

    async def aretrieve_with_details(
        self, query: str, filters: Dict[str, Any] = None
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Retrieve documents using hybrid BM25 + vector search with optional reranking.
        
        Args:
            query: The search query.
            filters: Metadata filters.
            
        Returns:
            Tuple of (chunks_with_scores, queries_used).
        """
        # Expand query for better recall (and UI display)
        queries = await self.multi_query_expander.aexpand_query(query)
        
        # Build BM25 index if needed
        if self.enable_hybrid and self.bm25_retriever is None:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._build_bm25_index)
        
        query_embedding = self._get_embedding(query)
        
        # Prepare query args
        query_args = {
            "vector": query_embedding,
            "top_k": self.rerank_top_n if (self.enable_hybrid or self.enable_reranker) else self.top_k,
            "include_metadata": True
        }
        if filters:
            query_args["filter"] = filters

        # Query Pinecone
        vector_results = self.index.query(**query_args)
        
        if self.enable_hybrid:
            loop = asyncio.get_event_loop()
            # Note: BM25 on Pinecone is done locally on cached documents.
            # We need to filter BM25 results manually if they are returned.
            # This implementation lazily builds BM25 from *some* docs. 
            bm25_docs = await loop.run_in_executor(
                None, 
                self.bm25_retriever.invoke,
                query
            )
            
            # Manual Filter for BM25
            if filters:
                bm25_docs = [
                    d for d in bm25_docs 
                    if all(d.metadata.get(k) == v for k, v in filters.items())
                ]
            
            chunks_with_scores = rrf_fusion(
                bm25_docs,
                vector_results['matches'],
                k=60
            )
            chunks_with_scores = chunks_with_scores[:self.rerank_top_n]
        else:
            chunks_with_scores = [
                pinecone_match_to_scored_chunk(match) 
                for match in vector_results['matches']
            ]
        
        # Apply cross-encoder reranking if enabled
        if self.enable_reranker and self.cross_encoder_reranker:
            # Rerank against the original query
            chunks_with_scores = self.cross_encoder_reranker.rerank(
                query, 
                chunks_with_scores,
                top_k=self.top_k
            )
        else:
            chunks_with_scores = chunks_with_scores[:self.top_k]
        
        return chunks_with_scores, queries
    
    def retrieve_with_details(
        self, query: str
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Sync version of aretrieve_with_details."""
        query_embedding = self._get_embedding(query)
        
        results = self.index.query(
            vector=query_embedding,
            top_k=self.top_k,
            include_metadata=True
        )
        
        chunks_with_scores = [
            pinecone_match_to_scored_chunk(match) 
            for match in results['matches']
        ]
        
        return chunks_with_scores, [query]
    
    def generate_answer(self, query: str, chunks_with_scores: List[Dict]) -> str:
        """Generate an answer from retrieved chunks."""
        return self.answer_generator.generate_answer(query, chunks_with_scores)
    
    async def agenerate_answer(self, query: str, chunks_with_scores: List[Dict]) -> str:
        """Async version of generate_answer."""
        return await self.answer_generator.agenerate_answer(query, chunks_with_scores)
    
    async def agenerate_answer_stream(
        self, query: str, chunks_with_scores: List[Dict]
    ) -> AsyncIterator[str]:
        """Stream the answer generation."""
        async for chunk in self.answer_generator.agenerate_answer_stream(
            query, chunks_with_scores
        ):
            yield chunk
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the Pinecone index."""
        return self.index.describe_index_stats()
