"""Core modules for DeepRecall."""

from .ingestion import (
    PDFPreprocessor,
    DocumentPartitioner,
    DocumentChunker,
    ContentSummarizer,
    IngestionPipeline,
    IngestionReport,
)
from .retrieval import (
    MultiQueryExpander,
    AnswerGenerator,
    PineconeRetrieverSystem,
)
from .protocols import RetrieverProtocol, IngestionPipelineProtocol
from .config import Settings, get_settings
from .logging_config import setup_logging, get_logger

__all__ = [
    # Ingestion
    "PDFPreprocessor",
    "DocumentPartitioner",
    "DocumentChunker",
    "ContentSummarizer",
    "IngestionPipeline",
    "IngestionReport",
    # Retrieval
    "MultiQueryExpander",
    "AnswerGenerator",
    "PineconeRetrieverSystem",
    # Infrastructure
    "RetrieverProtocol",
    "IngestionPipelineProtocol",
    "Settings",
    "get_settings",
    "setup_logging",
    "get_logger",
]

