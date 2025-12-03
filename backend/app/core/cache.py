"""
Redis-based caching middleware for FastAPI
Provides response caching for expensive API calls
"""
from functools import wraps
from typing import Optional, Callable
import json
import hashlib
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import redis
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """Manages Redis-based caching for API responses"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info("Redis cache connected successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Caching disabled.")
            self.redis_client = None
    
    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a unique cache key from function arguments"""
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        return f"cache:{hashlib.md5(key_data.encode()).hexdigest()}"
    
    def get(self, key: str) -> Optional[str]:
        """Get cached value"""
        if not self.redis_client:
            return None
        
        try:
            return self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: str, ttl: int = 300):
        """Set cached value with TTL (default 5 minutes)"""
        if not self.redis_client:
            return
        
        try:
            self.redis_client.setex(key, ttl, value)
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    def delete(self, pattern: str):
        """Delete cached values matching pattern"""
        if not self.redis_client:
            return
        
        try:
            keys = self.redis_client.keys(f"cache:{pattern}*")
            if keys:
                self.redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
    
    def invalidate_customer_cache(self, customer_id: str):
        """Invalidate all cache entries for a customer"""
        self.delete(f"customer:{customer_id}")
    
    def invalidate_marketplace_cache(self):
        """Invalidate marketplace listings cache"""
        self.delete("marketplace")

# Global cache manager instance
cache_manager = None

def init_cache(redis_url: str):
    """Initialize cache manager"""
    global cache_manager
    cache_manager = CacheManager(redis_url)
    return cache_manager

def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator for caching function results
    
    Args:
        ttl: Time to live in seconds (default 5 minutes)
        key_prefix: Prefix for cache key
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not cache_manager or not cache_manager.redis_client:
                # Cache disabled, call function directly
                return await func(*args, **kwargs)
            
            # Generate cache key
            cache_key = cache_manager._generate_cache_key(
                key_prefix or func.__name__,
                *args,
                **kwargs
            )
            
            # Try to get from cache
            cached_value = cache_manager.get(cache_key)
            if cached_value:
                logger.debug(f"Cache hit: {cache_key}")
                return json.loads(cached_value)
            
            # Cache miss, call function
            logger.debug(f"Cache miss: {cache_key}")
            result = await func(*args, **kwargs)
            
            # Store in cache
            cache_manager.set(cache_key, json.dumps(result), ttl)
            
            return result
        
        return wrapper
    return decorator

def cache_response(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator for caching FastAPI endpoint responses
    
    Usage:
        @router.get("/expensive-endpoint")
        @cache_response(ttl=600)
        async def expensive_endpoint():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request if present
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # No request object, can't cache
                return await func(*args, **kwargs)
            
            if not cache_manager or not cache_manager.redis_client:
                # Cache disabled
                return await func(*args, **kwargs)
            
            # Generate cache key from URL and query params
            cache_key = f"cache:{key_prefix or func.__name__}:{request.url.path}:{request.url.query}"
            cache_key = hashlib.md5(cache_key.encode()).hexdigest()
            
            # Try to get from cache
            cached_value = cache_manager.get(f"cache:{cache_key}")
            if cached_value:
                logger.debug(f"Response cache hit: {cache_key}")
                cached_data = json.loads(cached_value)
                return JSONResponse(content=cached_data)
            
            # Cache miss, call endpoint
            logger.debug(f"Response cache miss: {cache_key}")
            response = await func(*args, **kwargs)
            
            # Cache the response if it's successful
            if isinstance(response, (dict, list)):
                cache_manager.set(f"cache:{cache_key}", json.dumps(response), ttl)
            elif isinstance(response, JSONResponse):
                # Extract content from JSONResponse
                if hasattr(response, 'body'):
                    cache_manager.set(f"cache:{cache_key}", response.body.decode(), ttl)
            
            return response
        
        return wrapper
    return decorator

# Convenience functions for common cache operations
def invalidate_on_mutation(customer_id: Optional[str] = None):
    """Decorator to invalidate cache after mutations"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            if cache_manager and customer_id:
                cache_manager.invalidate_customer_cache(customer_id)
            
            return result
        return wrapper
    return decorator
