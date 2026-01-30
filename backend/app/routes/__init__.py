"""API Routes."""

from .ingestion import router as ingestion_router
from .chat import router as chat_router
from .system import router as system_router
from .aws_ingestion import router as aws_ingestion_router

__all__ = ["ingestion_router", "chat_router", "system_router", "aws_ingestion_router"]

