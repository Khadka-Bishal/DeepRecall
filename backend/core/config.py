"""Centralized configuration management for DeepRecall.

Uses pydantic-settings for type-safe environment variable parsing
with validation and sensible defaults.
"""

import os
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application configuration."""
    
    # API Keys (required in production)
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    pinecone_api_key: str = Field(default="", alias="PINECONE_API_KEY")
    langchain_api_key: str = Field(default="", alias="LANGCHAIN_API_KEY")
    wandb_api_key: str = Field(default="", alias="WANDB_API_KEY")
    
    # Pinecone Configuration
    pinecone_index_name: str = Field(default="deeprecall", alias="PINECONE_INDEX_NAME")
    use_pinecone: bool = Field(default=True, alias="USE_PINECONE")
    enable_hybrid_search: bool = Field(default=False, alias="ENABLE_HYBRID_SEARCH")
    enable_reranker: bool = Field(default=True, alias="ENABLE_RERANKER")
    
    # Rate Limiting
    max_concurrent_uploads: int = Field(default=10, alias="MAX_CONCURRENT_UPLOADS")
    max_requests_per_minute: int = Field(default=10, alias="MAX_REQUESTS_PER_MINUTE")
    max_file_size_mb: int = Field(default=5, alias="MAX_FILE_SIZE_MB")
    
    # Model Configuration
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")
    embedding_model: str = Field(default="text-embedding-3-small", alias="EMBEDDING_MODEL")
    embedding_dimension: int = Field(default=1536, alias="EMBEDDING_DIMENSION")
    llm_temperature: float = Field(default=0.0, alias="LLM_TEMPERATURE")
    
    # Retrieval Configuration
    retrieval_top_k: int = Field(default=5, alias="RETRIEVAL_TOP_K")
    rerank_top_n: int = Field(default=10, alias="RERANK_TOP_N")
    num_query_expansions: int = Field(default=3, alias="NUM_QUERY_EXPANSIONS")
    
    # Cache Configuration  
    cache_max_size: int = Field(default=100, alias="CACHE_MAX_SIZE")
    cache_ttl_seconds: int = Field(default=300, alias="CACHE_TTL_SECONDS")
    answer_cache_ttl_seconds: int = Field(default=600, alias="ANSWER_CACHE_TTL_SECONDS")
    
    # CORS Configuration
    allowed_origins: List[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000", "http://localhost:5174", "http://localhost:5175"],
        alias="ALLOWED_ORIGINS"
    )
    
    # Observability
    disable_observability: bool = Field(default=False, alias="DISABLE_OBSERVABILITY")
    langsmith_project: str = Field(default="DeepRecall", alias="LANGSMITH_PROJECT")
    wandb_project: str = Field(default="deeprecall", alias="WANDB_PROJECT")

    # AWS Configuration
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    input_bucket_name: str = Field(default="deeprecall-input-dev", alias="DEEPRECALL_INPUT_BUCKET")
    output_bucket_name: str = Field(default="deeprecall-output-dev", alias="DEEPRECALL_OUTPUT_BUCKET")
    use_aws_pipeline: bool = Field(default=False, alias="USE_AWS_PIPELINE")
    
    model_config = {
        "env_file": ".env" if os.path.exists(".env") else None,
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "populate_by_name": True,
        "protected_namespaces": (),
    }

    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.
    
    Uses lru_cache to ensure settings are only loaded once per process.
    Call get_settings.cache_clear() to reload settings if needed.
    """
    return Settings()
