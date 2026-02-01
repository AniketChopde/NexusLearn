"""
Token Bucket algorithm for rate limiting
Prevents API abuse and ensures fair resource allocation
"""

import time
import asyncio
from typing import Optional
from loguru import logger


class TokenBucket:
    """
    Token Bucket rate limiting algorithm.
    
    Algorithm: Token Bucket
    Time Complexity: O(1) for acquire operation
    Space Complexity: O(1)
    
    Advantages over alternatives:
    - Allows bursts (vs Leaky Bucket)
    - Simple implementation (vs Sliding Window)
    - Memory efficient (vs Fixed Window)
    
    Example:
        limiter = TokenBucket(capacity=100, refill_rate=10)  # 10 tokens/sec
        if await limiter.acquire(tokens=5):
            # Process request
            pass
        else:
            # Rate limit exceeded
            raise HTTPException(429, "Too many requests")
    """
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.
        
        Args:
            capacity: Maximum number of tokens in bucket
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.tokens = float(capacity)
        self.refill_rate = refill_rate
        self.last_refill = time.time()
        self.lock = asyncio.Lock()
        
        logger.info(f"Initialized TokenBucket: capacity={capacity}, rate={refill_rate}/s")
        
    async def acquire(self, tokens: int = 1, blocking: bool = False) -> bool:
        """
        Try to acquire tokens from the bucket.
        
        Args:
            tokens: Number of tokens to acquire
            blocking: If True, wait until tokens are available
            
        Returns:
            True if tokens were acquired, False otherwise
        """
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_refill
            
            # Refill tokens based on elapsed time
            new_tokens = elapsed * self.refill_rate
            self.tokens = min(self.capacity, self.tokens + new_tokens)
            self.last_refill = now
            
            # Try to consume tokens
            if self.tokens >= tokens:
                self.tokens -= tokens
                logger.debug(f"Acquired {tokens} tokens. Remaining: {self.tokens:.2f}")
                return True
            
            # If blocking, wait for refill
            if blocking:
                wait_time = (tokens - self.tokens) / self.refill_rate
                logger.debug(f"Blocking for {wait_time:.2f}s to acquire {tokens} tokens")
                await asyncio.sleep(wait_time)
                # Recursive call after waiting
                return await self.acquire(tokens, blocking=False)
            
            logger.debug(f"Rate limit exceeded. Available: {self.tokens:.2f}, Requested: {tokens}")
            return False
            
    async def wait_for_tokens(self, tokens: int = 1) -> float:
        """
        Calculate wait time until tokens are available.
        
        Args:
            tokens: Number of tokens needed
            
        Returns:
            Wait time in seconds (0 if tokens are available)
        """
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_refill
            
            # Calculate tokens after refill
            new_tokens = elapsed * self.refill_rate
            available = min(self.capacity, self.tokens + new_tokens)
            
            if available >= tokens:
                return 0.0
            
            # Calculate wait time
            needed = tokens - available
            wait_time = needed / self.refill_rate
            return wait_time
            
    def get_stats(self) -> dict:
        """Get current bucket statistics."""
        now = time.time()
        elapsed = now - self.last_refill
        available = min(self.capacity, self.tokens + (elapsed * self.refill_rate))
        
        return {
            "capacity": self.capacity,
            "tokens": available,
            "refill_rate": self.refill_rate,
            "fill_percentage": (available / self.capacity) * 100
        }


class RateLimiter:
    """
    Multi-tier rate limiter with different limits for different resources.
    
    Example:
        limiter = RateLimiter()
        limiter.add_bucket("api", capacity=100, refill_rate=10)
        limiter.add_bucket("embeddings", capacity=50, refill_rate=5)
        
        if await limiter.check("api", user_id="123"):
            # Process API request
            pass
    """
    
    def __init__(self):
        self.buckets: dict[str, dict[str, TokenBucket]] = {}
        self.global_buckets: dict[str, TokenBucket] = {}
        
    def add_global_bucket(self, name: str, capacity: int, refill_rate: float):
        """Add a global rate limit (applies to all users)."""
        self.global_buckets[name] = TokenBucket(capacity, refill_rate)
        logger.info(f"Added global bucket '{name}'")
        
    def add_user_bucket(
        self, 
        bucket_type: str, 
        user_id: str, 
        capacity: int, 
        refill_rate: float
    ):
        """Add a per-user rate limit."""
        if bucket_type not in self.buckets:
            self.buckets[bucket_type] = {}
        
        self.buckets[bucket_type][user_id] = TokenBucket(capacity, refill_rate)
        logger.debug(f"Added user bucket '{bucket_type}' for user {user_id}")
        
    async def check(
        self, 
        bucket_type: str, 
        user_id: Optional[str] = None, 
        tokens: int = 1,
        blocking: bool = False
    ) -> bool:
        """
        Check both global and user-specific rate limits.
        
        Args:
            bucket_type: Type of bucket (e.g., "api", "embeddings")
            user_id: User identifier (optional)
            tokens: Number of tokens to acquire
            blocking: Whether to wait for tokens
            
        Returns:
            True if rate limit passed, False otherwise
        """
        # Check global limit first
        if bucket_type in self.global_buckets:
            if not await self.global_buckets[bucket_type].acquire(tokens, blocking):
                logger.warning(f"Global rate limit exceeded for '{bucket_type}'")
                return False
        
        # Check user-specific limit
        if user_id and bucket_type in self.buckets:
            if user_id not in self.buckets[bucket_type]:
                # Auto-create bucket with default settings
                # You can customize these defaults
                self.buckets[bucket_type][user_id] = TokenBucket(
                    capacity=100,
                    refill_rate=10
                )
            
            if not await self.buckets[bucket_type][user_id].acquire(tokens, blocking):
                logger.warning(f"User rate limit exceeded for user {user_id}, bucket '{bucket_type}'")
                return False
        
        return True
        
    def get_all_stats(self) -> dict:
        """Get statistics for all buckets."""
        stats = {
            "global": {name: bucket.get_stats() for name, bucket in self.global_buckets.items()},
            "users": {}
        }
        
        for bucket_type, users in self.buckets.items():
            stats["users"][bucket_type] = {
                user_id: bucket.get_stats() 
                for user_id, bucket in users.items()
            }
        
        return stats


# Global rate limiter instance
rate_limiter = RateLimiter()

# Initialize with default buckets
rate_limiter.add_global_bucket("api", capacity=1000, refill_rate=100)  # 100 req/s globally
rate_limiter.add_global_bucket("embeddings", capacity=500, refill_rate=50)  # 50 req/s
rate_limiter.add_global_bucket("llm", capacity=200, refill_rate=20)  # 20 req/s
