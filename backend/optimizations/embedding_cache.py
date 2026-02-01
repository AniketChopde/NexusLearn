"""
LRU Cache with TTL for embeddings
Reduces Azure OpenAI API calls by 70-90%
"""

from collections import OrderedDict
from typing import List, Optional
import hashlib
import time
from loguru import logger


class EmbeddingCache:
    """
    LRU (Least Recently Used) cache with TTL for embeddings.
    
    Time Complexity: O(1) for get/set operations
    Space Complexity: O(k) where k = max_size
    
    Data Structure: OrderedDict (doubly-linked list + hash table)
    """
    
    def __init__(self, max_size: int = 10000, ttl: int = 3600):
        """
        Initialize embedding cache.
        
        Args:
            max_size: Maximum number of cached embeddings (default: 10,000)
            ttl: Time-to-live in seconds (default: 1 hour)
        """
        self.cache = OrderedDict()
        self.max_size = max_size
        self.ttl = ttl
        self.timestamps = {}
        
        # Metrics
        self.hits = 0
        self.misses = 0
        
        logger.info(f"Initialized EmbeddingCache with max_size={max_size}, ttl={ttl}s")
        
    def _hash(self, text: str) -> str:
        """Generate cache key from text using SHA-256."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]
        
    def get(self, text: str) -> Optional[List[float]]:
        """
        Get embedding from cache.
        
        Args:
            text: Input text to look up
            
        Returns:
            Cached embedding vector or None if not found/expired
        """
        key = self._hash(text)
        
        if key in self.cache:
            # Check TTL
            if time.time() - self.timestamps[key] < self.ttl:
                # Move to end (mark as recently used)
                self.cache.move_to_end(key)
                self.hits += 1
                
                if self.hits % 100 == 0:
                    logger.debug(f"Cache hit rate: {self.hit_rate():.2%}")
                
                return self.cache[key]
            else:
                # Expired, remove from cache
                del self.cache[key]
                del self.timestamps[key]
                logger.debug(f"Expired cache entry for key {key}")
        
        self.misses += 1
        return None
        
    def set(self, text: str, embedding: List[float]):
        """
        Store embedding in cache.
        
        Args:
            text: Input text
            embedding: Embedding vector to cache
        """
        key = self._hash(text)
        
        # Evict least recently used if cache is full
        if len(self.cache) >= self.max_size and key not in self.cache:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            del self.timestamps[oldest_key]
            logger.debug(f"Evicted LRU entry {oldest_key}")
        
        self.cache[key] = embedding
        self.timestamps[key] = time.time()
        self.cache.move_to_end(key)
        
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total
        
    def get_stats(self) -> dict:
        """Get cache statistics."""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hit_rate(),
            "ttl": self.ttl
        }
        
    def clear(self):
        """Clear all cached embeddings."""
        self.cache.clear()
        self.timestamps.clear()
        self.hits = 0
        self.misses = 0
        logger.info("Cache cleared")


# Global cache instance
embedding_cache = EmbeddingCache(max_size=10000, ttl=3600)
