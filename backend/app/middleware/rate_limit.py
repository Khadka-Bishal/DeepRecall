"""Rate limiting middleware for DeepRecall API."""

import logging
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from core.config import get_settings

log = logging.getLogger(__name__)


class RateLimiter:
    """Global rate limiter with configurable limits.
    
    Provides:
    - Max concurrent ingestions (global semaphore)
    - Per-IP request throttling (sliding window)
    """
    
    _instance = None
    
    def __new__(cls):
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize rate limiter with settings."""
        if self._initialized:
            return
            
        settings = get_settings()
        
        # Global concurrency semaphore
        self.global_semaphore = asyncio.Semaphore(settings.max_concurrent_uploads)
        
        # Per-IP request tracking
        self.request_history: Dict[str, List[datetime]] = defaultdict(list)
        
        # Limits from settings
        self.max_requests_per_minute = settings.max_requests_per_minute
        self.window_seconds = 60
        
        log.info(
            "Rate limiter initialized: concurrent=%d, per-ip=%d/min",
            settings.max_concurrent_uploads,
            self.max_requests_per_minute
        )
        
        self._initialized = True
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check X-Forwarded-For first (for proxies/load balancers)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _cleanup_old_requests(self, ip: str) -> None:
        """Remove requests older than the time window."""
        cutoff = datetime.now() - timedelta(seconds=self.window_seconds)
        self.request_history[ip] = [
            ts for ts in self.request_history[ip] if ts > cutoff
        ]
    
    def check_rate_limit(self, ip: str) -> bool:
        """Check if IP has exceeded rate limit.
        
        Returns:
            True if allowed, False if rate limited.
        """
        self._cleanup_old_requests(ip)
        
        if len(self.request_history[ip]) >= self.max_requests_per_minute:
            return False
        
        self.request_history[ip].append(datetime.now())
        return True


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limits on ingestion endpoints."""
    
    def __init__(self, app):
        super().__init__(app)
        self.rate_limiter = RateLimiter()
    
    async def dispatch(self, request: Request, call_next):
        """Process request through rate limiting."""
        # Only rate-limit the /ingest endpoint
        if request.url.path == "/ingest" and request.method == "POST":
            client_ip = self.rate_limiter._get_client_ip(request)
            
            # Check per-IP rate limit
            if not self.rate_limiter.check_rate_limit(client_ip):
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Max {self.rate_limiter.max_requests_per_minute} requests per minute."
                )
            
            # Acquire global semaphore for concurrent limit
            async with self.rate_limiter.global_semaphore:
                response = await call_next(request)
                return response
        
        # All other endpoints pass through
        return await call_next(request)
