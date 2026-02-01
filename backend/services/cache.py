"""
Redis cache service for session management and caching.
"""

import redis.asyncio as redis
import json
from typing import Any, Optional, Dict, List
from loguru import logger
from datetime import datetime

from config import settings


class CacheService:
    """Service for Redis caching and session management."""
    
    def __init__(self):
        """Initialize Redis client."""
        self.redis_client: Optional[redis.Redis] = None
        self.default_ttl = settings.redis_cache_ttl
        self.is_ready = False
        self._memory_fallback: Dict[str, Any] = {}
        self._connection_failed = False
    
    async def connect(self):
        """Connect to Redis."""
        try:
            from asyncio import Lock
            if not hasattr(self, '_lock'):
                self._lock = Lock()
            
            async with self._lock:
                if self._connection_failed or self.is_ready:
                    return

                self.redis_client = await redis.from_url(
                    settings.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=1  # 1s is enough for local/cloud
                )
                await self.redis_client.ping()
                self.is_ready = True
                logger.info("Connected to Redis successfully")
        except Exception as e:
            self._connection_failed = True
            self.is_ready = False
            logger.warning(f"Redis not available, using in-memory fallback. (Skipping further logs)")
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        """
        try:
            if not self.is_ready and not self._connection_failed:
                await self.connect()
            
            if self.is_ready and self.redis_client:
                value = await self.redis_client.get(key)
                if value:
                    return json.loads(value)
            else:
                return self._memory_fallback.get(key)
            return None
        
        except Exception as e:
            if self.is_ready:
                logger.error(f"Error getting from cache: {str(e)}")
            return self._memory_fallback.get(key)
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.
        """
        try:
            if not self.is_ready and not self._connection_failed:
                await self.connect()
            
            # Always update memory fallback for safety
            self._memory_fallback[key] = value
            
            if self.is_ready and self.redis_client:
                ttl = ttl or self.default_ttl
                serialized_value = json.dumps(value)
                await self.redis_client.setex(key, ttl, serialized_value)
            
            return True
        
        except Exception as e:
            if self.is_ready:
                logger.error(f"Error setting cache: {str(e)}")
            return True # Still return True because memory fallback worked
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        """
        try:
            if key in self._memory_fallback:
                del self._memory_fallback[key]
                
            if self.is_ready and self.redis_client:
                await self.redis_client.delete(key)
            return True
        
        except Exception as e:
            if self.is_ready:
                logger.error(f"Error deleting from cache: {str(e)}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        """
        try:
            if key in self._memory_fallback:
                return True
                
            if self.is_ready and self.redis_client:
                return await self.redis_client.exists(key) > 0
            return False
        
        except Exception as e:
            return key in self._memory_fallback
    
    # Search-specific methods
    async def cache_search_results(
        self,
        query_hash: str,
        query: str,
        results: List[Dict[str, Any]]
    ) -> bool:
        """
        Cache search results.
        
        Args:
            query_hash: Hash of the query
            query: Original query
            results: Search results
        
        Returns:
            True if successful
        """
        cache_data = {
            "query": query,
            "results": results,
            "cached_at": datetime.utcnow().isoformat()
        }
        
        return await self.set(f"search:{query_hash}", cache_data)
    
    async def get_search_results(self, query_hash: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached search results.
        
        Args:
            query_hash: Hash of the query
        
        Returns:
            Cached search results or None
        """
        cache_data = await self.get(f"search:{query_hash}")
        if cache_data:
            return cache_data.get("results")
        return None
    
    # Session-specific methods
    async def set_session(
        self,
        session_id: str,
        data: Dict[str, Any],
        ttl: int = 3600
    ) -> bool:
        """
        Set session data.
        
        Args:
            session_id: Session identifier
            data: Session data
            ttl: Time to live in seconds (default: 1 hour)
        
        Returns:
            True if successful
        """
        return await self.set(f"session:{session_id}", data, ttl)
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Session data or None
        """
        return await self.get(f"session:{session_id}")
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            True if successful
        """
        return await self.delete(f"session:{session_id}")


# Global service instance
cache_service = CacheService()
