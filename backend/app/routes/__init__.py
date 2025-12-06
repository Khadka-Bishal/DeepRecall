"""API Routes."""

from .ingestion import router as ingestion_router
from .chat import router as chat_router
from .system import router as system_router

__all__ = ["ingestion_router", "chat_router", "system_router"]
