from __future__ import annotations
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from core.retrieval import PineconeRetrieverSystem
    from core.ingestion import IngestionPipeline
    from app.services.observability import ObservabilityManager


class AppState:
    _inst: Optional[AppState] = None

    def __init__(self):
        self.retriever: Optional[PineconeRetrieverSystem] = None
        self.pipeline: Optional[IngestionPipeline] = None
        self.obs: Optional[ObservabilityManager] = None

    @classmethod
    def inst(cls) -> AppState:
        if cls._inst is None:
            cls._inst = cls()
        return cls._inst

    def initialize(self, retriever, pipeline, obs=None):
        self.retriever = retriever
        self.pipeline = pipeline
        self.obs = obs


def get_app_state() -> AppState:
    return AppState.inst()


def get_retriever_system():
    s = get_app_state()
    if not s.retriever:
        raise RuntimeError("retriever not initialized")
    return s.retriever


def get_ingestion_pipeline():
    s = get_app_state()
    if not s.pipeline:
        raise RuntimeError("pipeline not initialized")
    return s.pipeline


def get_observability():
    return get_app_state().obs
