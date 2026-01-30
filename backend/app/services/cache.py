"""Caching layer for DeepRecall queries and answers."""

import hashlib
import logging
import time
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import OrderedDict
from threading import Lock

from core.config import get_settings

log = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """A single cache entry with TTL support."""
    value: Any
    created_at: float
    ttl_seconds: float
    hits: int = 0

    @property
    def is_expired(self) -> bool:
        """Check if entry has exceeded its TTL."""
        return time.time() > (self.created_at + self.ttl_seconds)

    @property
    def age_seconds(self) -> float:
        """Get age of entry in seconds."""
        return time.time() - self.created_at

    @property
    def time_remaining(self) -> float:
        """Get remaining TTL in seconds."""
        return max(0, (self.created_at + self.ttl_seconds) - time.time())


class QueryCache:
    """LRU cache with TTL support for query results.
    
    Thread-safe implementation using OrderedDict for LRU ordering
    with configurable max size and TTL.
    """
    
    def __init__(
        self,
        max_size: int = 100,
        default_ttl_seconds: float = 300,
        enable_stats: bool = True,
    ):
        """Initialize the cache.
        
        Args:
            max_size: Maximum entries before LRU eviction.
            default_ttl_seconds: Default TTL for entries.
            enable_stats: Whether to track hit/miss statistics.
        """
        self.max_size = max_size
        self.default_ttl = default_ttl_seconds
        self.enable_stats = enable_stats
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = Lock()

        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expirations": 0,
        }

    def _generate_key(self, query: str, prefix: str = "") -> str:
        """Generate cache key from query string."""
        normalized = query.lower().strip()
        h = hashlib.md5(normalized.encode()).hexdigest()[:16]
        return f"{prefix}:{h}" if prefix else h

    def get(self, query: str, prefix: str = "") -> Tuple[Optional[Any], bool]:
        """Get value from cache.
        
        Returns:
            Tuple of (value, hit) where hit indicates cache hit.
        """
        key = self._generate_key(query, prefix)

        with self._lock:
            if key not in self._cache:
                if self.enable_stats:
                    self._stats["misses"] += 1
                return None, False

            entry = self._cache[key]

            if entry.is_expired:
                del self._cache[key]
                if self.enable_stats:
                    self._stats["expirations"] += 1
                    self._stats["misses"] += 1
                return None, False

            # Cache hit - update LRU order
            self._cache.move_to_end(key)
            entry.hits += 1
            if self.enable_stats:
                self._stats["hits"] += 1

            return entry.value, True

    def set(
        self,
        query: str,
        value: Any,
        prefix: str = "",
        ttl_seconds: Optional[float] = None,
    ) -> None:
        """Set value in cache."""
        key = self._generate_key(query, prefix)
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl

        with self._lock:
            # Evict oldest if at capacity
            while len(self._cache) >= self.max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                if self.enable_stats:
                    self._stats["evictions"] += 1

            self._cache[key] = CacheEntry(
                value=value, 
                created_at=time.time(), 
                ttl_seconds=ttl, 
                hits=0
            )

    def invalidate(self, query: str, prefix: str = "") -> bool:
        """Invalidate a specific cache entry."""
        key = self._generate_key(query, prefix)
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> int:
        """Clear all entries and return count cleared."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            return count

    def cleanup_expired(self) -> int:
        """Remove all expired entries."""
        removed = 0
        with self._lock:
            expired_keys = [k for k, v in self._cache.items() if v.is_expired]
            for key in expired_keys:
                del self._cache[key]
                removed += 1
                if self.enable_stats:
                    self._stats["expirations"] += 1
        return removed

    @property
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = (
                self._stats["hits"] / total_requests * 100 if total_requests > 0 else 0
            )

            return {
                **self._stats,
                "current_size": len(self._cache),
                "max_size": self.max_size,
                "hit_rate_percent": round(hit_rate, 2),
                "total_requests": total_requests,
            }

    def get_entry_info(self, query: str, prefix: str = "") -> Optional[Dict[str, Any]]:
        """Get metadata about a specific cache entry."""
        key = self._generate_key(query, prefix)
        with self._lock:
            if key not in self._cache:
                return None
            entry = self._cache[key]
            return {
                "age_seconds": round(entry.age_seconds, 2),
                "time_remaining_seconds": round(entry.time_remaining, 2),
                "hits": entry.hits,
                "is_expired": entry.is_expired,
            }


# Cache instances (lazy initialization)
_retrieval_cache: Optional[QueryCache] = None
_answer_cache: Optional[QueryCache] = None


def get_retrieval_cache() -> QueryCache:
    """Get the retrieval cache singleton."""
    global _retrieval_cache
    if _retrieval_cache is None:
        settings = get_settings()
        _retrieval_cache = QueryCache(
            max_size=settings.cache_max_size,
            default_ttl_seconds=settings.cache_ttl_seconds,
        )
        log.info("Retrieval cache initialized")
    return _retrieval_cache


def get_answer_cache() -> QueryCache:
    """Get the answer cache singleton."""
    global _answer_cache
    if _answer_cache is None:
        settings = get_settings()
        _answer_cache = QueryCache(
            max_size=settings.cache_max_size // 2,
            default_ttl_seconds=settings.answer_cache_ttl_seconds,
        )
        log.info("Answer cache initialized")
    return _answer_cache


def get_cache_stats() -> Dict[str, Any]:
    """Get statistics for all caches."""
    return {
        "retrieval_cache": get_retrieval_cache().stats,
        "answer_cache": get_answer_cache().stats,
    }


def clear_all_caches() -> Dict[str, int]:
    """Clear all caches and return counts."""
    return {
        "retrieval_cleared": get_retrieval_cache().clear(),
        "answer_cleared": get_answer_cache().clear(),
    }
