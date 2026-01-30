"""Core protocols and interfaces for DeepRecall retrieval systems.

This module defines abstract protocols using typing.Protocol to ensure
all retriever implementations follow consistent interfaces.
"""

from typing import Protocol, List, Dict, Any, Tuple, AsyncIterator, runtime_checkable
from langchain_core.documents import Document


@runtime_checkable
class RetrieverProtocol(Protocol):
    """Base protocol that all retriever implementations must follow.
    
    This ensures consistent API across HybridRetrieverSystem, 
    PineconeRetrieverSystem, and any future implementations.
    """
    
    def initialize_vector_store(self, documents: List[Document]) -> Any:
        """Initialize or update the vector store with documents.
        
        Args:
            documents: List of LangChain Document objects to index.
            
        Returns:
            The initialized vector store instance.
        """
        ...
    
    async def aretrieve_with_details(
        self, query: str
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Retrieve documents with detailed scoring information.
        
        Args:
            query: The search query string.
            
        Returns:
            Tuple of (chunks_with_scores, queries_used) where:
            - chunks_with_scores: List of dicts with 'document', 'score', 'scores' keys
            - queries_used: List of query strings used (original + expanded)
        """
        ...
    
    async def agenerate_answer(
        self, query: str, chunks_with_scores: List[Dict]
    ) -> str:
        """Generate an answer from retrieved chunks.
        
        Args:
            query: The original user query.
            chunks_with_scores: Retrieved chunks with scoring metadata.
            
        Returns:
            Generated answer string.
        """
        ...
    
    async def agenerate_answer_stream(
        self, query: str, chunks_with_scores: List[Dict]
    ) -> AsyncIterator[str]:
        """Stream the answer generation token by token.
        
        Args:
            query: The original user query.
            chunks_with_scores: Retrieved chunks with scoring metadata.
            
        Yields:
            Answer tokens as they are generated.
        """
        ...


@runtime_checkable
class IngestionPipelineProtocol(Protocol):
    """Protocol for document ingestion pipeline implementations."""
    
    async def run(
        self, file_path: str, manager: Any = None
    ) -> Dict[str, Any]:
        """Run the full ingestion pipeline on a document.
        
        Args:
            file_path: Path to the document to process.
            manager: Optional WebSocket manager for progress updates.
            
        Returns:
            Dict containing 'documents' and 'report' keys.
        """
        ...
