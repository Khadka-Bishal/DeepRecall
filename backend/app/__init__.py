"""DeepRecall Application Package."""

from .schemas import QueryRequest, ChunkResponse
from .websocket import ConnectionManager, get_connection_manager
from .services import (
    get_benchmark,
    get_observability_manager,
    get_retrieval_cache,
    get_answer_cache,
    get_cache_stats,
    clear_all_caches,
)
from .routes import ingestion_router, chat_router, system_router
from .state import (
    get_app_state,
    get_retriever_system,
    get_ingestion_pipeline,
    get_observability,
)

__all__ = [
    # Schemas
    "QueryRequest",
    "ChunkResponse",
    # WebSocket
    "ConnectionManager",
    "get_connection_manager",
    # Services
    "get_benchmark",
    "get_observability_manager",
    "get_retrieval_cache",
    "get_answer_cache",
    "get_cache_stats",
    "clear_all_caches",
    # Routes
    "ingestion_router",
    "chat_router",
    "system_router",
    # State
    "get_app_state",
    "get_retriever_system",
    "get_ingestion_pipeline",
    "get_observability",
]
