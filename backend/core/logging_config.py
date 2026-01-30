"""Standardized logging configuration for DeepRecall.
"""

import logging
import sys
from typing import Optional


def setup_logging(
    level: str = "INFO",
    format_string: Optional[str] = None,
    include_timestamp: bool = True
) -> None:
    """Configure application-wide logging.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        format_string: Custom format string. If None, uses sensible default.
        include_timestamp: Whether to include timestamps in log output.
    """
    if format_string is None:
        if include_timestamp:
            format_string = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        else:
            format_string = "[%(levelname)s] %(name)s: %(message)s"
    
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=format_string,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True  # Override any existing configuration
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given module name.
    
    Convenience wrapper that ensures consistent logger naming.
    
    Args:
        name: Usually __name__ from the calling module.
        
    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)
