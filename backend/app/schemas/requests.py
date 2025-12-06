"""Request/Response schemas for the API."""

from pydantic import BaseModel
from typing import List, Optional, Dict


class QueryRequest(BaseModel):
    """Request schema for chat queries."""

    query: str


class ChunkResponse(BaseModel):
    """Response schema for retrieved chunks."""

    id: str
    content: str
    page: Optional[int] = 1
    score: Optional[float] = 0.0
    scores: Optional[Dict[str, float]] = None
    images: List[str] = []


class HealthResponse(BaseModel):
    """Response schema for health check."""

    status: str
    service: str


class CacheStatsResponse(BaseModel):
    """Response schema for cache statistics."""

    retrieval_cache: Dict
    answer_cache: Dict


class BenchmarkResponse(BaseModel):
    """Response schema for benchmark metrics."""

    ingestion_runs: List[Dict]
    retrieval_runs: List[Dict]
    summary: Dict
