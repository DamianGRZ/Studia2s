"""
Semantic Cache System
Caches responses based on semantic similarity of queries
"""
import numpy as np
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict
import logging

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis not available, semantic cache will use in-memory storage")

from config.settings import settings

logger = logging.getLogger(__name__)


class SemanticCache:
    """
    Caches responses based on semantic similarity of queries.
    Dramatically reduces API costs for similar/repeated questions.
    """

    def __init__(self, vector_store: 'VectorStore', use_redis: bool = True):
        """
        Initialize semantic cache.

        Args:
            vector_store: FAISS vector store for similarity search
            use_redis: Whether to use Redis for persistence
        """
        self.vector_store = vector_store
        self.cache_hit_threshold = settings.CACHE_HIT_THRESHOLD
        self.max_cache_size = settings.MAX_CACHE_SIZE
        self.ttl_hours = settings.CACHE_TTL_HOURS

        # Initialize storage backend
        if use_redis and REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD,
                    decode_responses=True
                )
                self.redis_client.ping()
                self.use_redis = True
                logger.info("Semantic cache using Redis backend")
            except (redis.ConnectionError, redis.TimeoutError) as e:
                logger.warning(f"Redis connection failed: {e}. Using in-memory cache")
                self.use_redis = False
                self._memory_cache = {}
        else:
            self.use_redis = False
            self._memory_cache = {}
            logger.info("Semantic cache using in-memory backend")

        self.stats = {
            "hits": 0,
            "misses": 0,
            "total_queries": 0
        }

    async def get(
        self,
        query: str,
        query_embedding: np.ndarray
    ) -> Tuple[Optional[Dict], float]:
        """
        Attempts to retrieve cached response for semantically similar query.

        Args:
            query: User query string
            query_embedding: Embedding vector for the query

        Returns:
            (cached_response_dict, similarity_score) if hit, else (None, 0)
        """
        self.stats["total_queries"] += 1

        # Search vector store for similar queries
        similar_queries = self.vector_store.search(
            query_embedding,
            k=1,
            threshold=self.cache_hit_threshold
        )

        if not similar_queries:
            self.stats["misses"] += 1
            return None, 0.0

        query_id, similarity = similar_queries[0]

        # Retrieve cached response
        cached_data = self._get_from_backend(query_id)

        if not cached_data:
            self.stats["misses"] += 1
            return None, 0.0

        # Check TTL
        cached_time = datetime.fromisoformat(cached_data["timestamp"])
        if datetime.now() - cached_time > timedelta(hours=self.ttl_hours):
            self._delete_from_backend(query_id)
            self.stats["misses"] += 1
            logger.debug(f"Cache entry expired for query_id: {query_id}")
            return None, 0.0

        # Cache hit!
        self.stats["hits"] += 1
        logger.info(
            f"CACHE HIT: similarity={similarity:.3f}, "
            f"original='{cached_data['query']}', current='{query}'"
        )

        # Update hit count
        cached_data["hit_count"] = cached_data.get("hit_count", 0) + 1
        self._set_to_backend(query_id, cached_data)

        return cached_data, similarity

    async def set(
        self,
        query: str,
        query_embedding: np.ndarray,
        response: Dict
    ):
        """
        Stores query-response pair in semantic cache.

        Args:
            query: User query string
            query_embedding: Embedding vector for the query
            response: Response dictionary to cache
        """
        query_id = self._generate_query_id(query)

        # Add to vector store
        self.vector_store.add(query_id, query_embedding)

        # Prepare cache entry
        cache_entry = {
            "query": query,
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "hit_count": 0
        }

        # Store in backend
        self._set_to_backend(query_id, cache_entry)

        # Enforce max size if using in-memory cache
        if not self.use_redis:
            self._evict_lru()

        logger.debug(f"Cached response for query: '{query}'")

    def _generate_query_id(self, query: str) -> str:
        """Generate unique ID for query."""
        return hashlib.sha256(query.encode()).hexdigest()[:16]

    def _get_from_backend(self, query_id: str) -> Optional[Dict]:
        """Retrieve from storage backend."""
        if self.use_redis:
            data = self.redis_client.get(f"cache:{query_id}")
            return json.loads(data) if data else None
        else:
            return self._memory_cache.get(query_id)

    def _set_to_backend(self, query_id: str, data: Dict):
        """Store to storage backend."""
        if self.use_redis:
            self.redis_client.setex(
                f"cache:{query_id}",
                timedelta(hours=self.ttl_hours),
                json.dumps(data)
            )
        else:
            self._memory_cache[query_id] = data

    def _delete_from_backend(self, query_id: str):
        """Delete from storage backend."""
        if self.use_redis:
            self.redis_client.delete(f"cache:{query_id}")
        else:
            self._memory_cache.pop(query_id, None)

    def _evict_lru(self):
        """Evict least recently used entries (in-memory cache only)."""
        if len(self._memory_cache) <= self.max_cache_size:
            return

        # Sort by timestamp (oldest first)
        sorted_entries = sorted(
            self._memory_cache.items(),
            key=lambda x: (
                x[1].get("hit_count", 0),
                datetime.fromisoformat(x[1]["timestamp"])
            )
        )

        # Remove oldest 10%
        to_remove = int(self.max_cache_size * 0.1)
        for query_id, _ in sorted_entries[:to_remove]:
            del self._memory_cache[query_id]

        logger.info(f"Evicted {to_remove} entries from cache")

    def get_stats(self) -> Dict:
        """Get cache statistics."""
        total = self.stats["total_queries"]
        hit_rate = (self.stats["hits"] / total * 100) if total > 0 else 0

        return {
            "total_queries": total,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate_percent": round(hit_rate, 2),
            "backend": "redis" if self.use_redis else "memory",
            "cache_size": self._get_cache_size()
        }

    def _get_cache_size(self) -> int:
        """Get current cache size."""
        if self.use_redis:
            return self.redis_client.dbsize()
        else:
            return len(self._memory_cache)

    def clear(self):
        """Clear all cache entries."""
        if self.use_redis:
            self.redis_client.flushdb()
        else:
            self._memory_cache.clear()

        logger.info("Cache cleared")
