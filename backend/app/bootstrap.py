import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from core.config import get_settings
from core.ingestion import IngestionPipeline
from core.retrieval import PineconeRetrieverSystem
from app.state import get_app_state
from app.services import get_observability_manager

log = logging.getLogger(__name__)


def _init_observability() -> None:
    """Initialize observability systems."""
    settings = get_settings()
    
    if settings.disable_observability:
        return
    
    try:
        obs = get_observability_manager()
        obs.setup_langsmith(settings.langsmith_project)
        # Note: W&B config uses hardcoded retrieval type for tracking
        obs.setup_wandb(
            settings.wandb_project,
            config={
                "model": settings.llm_model,
                "embedding_model": settings.embedding_model,
                "retrieval": "pinecone_hybrid",
            },
        )
        return obs
    except Exception as e:
        log.warning(f"Observability skipped: {e}")
        return None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager."""
    settings = get_settings()
    
    # Initialize Core Systems
    retriever = PineconeRetrieverSystem()
    pipeline = IngestionPipeline(
        retriever_system=None if settings.use_aws_pipeline else retriever
    )
    obs = _init_observability()

    # Hydrate Global State
    get_app_state().initialize(retriever, pipeline, obs)
    
    log.info("System initialized")
    
    yield
    
    if obs:
        obs.finish()
    log.info("System shutdown")
