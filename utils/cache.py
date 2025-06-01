import redis
import json
import hashlib
import os
from typing import Optional, List, Any
from loguru import logger

# Redis connection with fallback to local development
try:
    REDIS_URL = os.getenv("REDIS_URL")
    if REDIS_URL:
        # Production Redis (from Redis Cloud, Railway, etc.)
        redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        logger.info("✅ Connected to Redis Cloud")
    else:
        # Local Redis for development
        redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        logger.info("✅ Connected to local Redis")
    
    # Test the connection
    redis_client.ping()
    
except Exception as e:
    logger.error(f"❌ Redis connection failed: {e}")
    logger.info("📋 Falling back to in-memory cache")
    redis_client = None

# In-memory fallback cache
memory_cache = {}

# Cache TTL settings (in seconds)
EMBEDDING_TTL = 24 * 60 * 60  # 24 hours
MATCH_TTL = 60 * 60           # 1 hour

def get_cached_embedding(text: str) -> Optional[List[float]]:
    """Get cached embedding for text"""
    try:
        key = f"embed:{text}"
        
        if redis_client:
            cached = redis_client.get(key)
            if cached:
                return json.loads(cached)
        else:
            # Fallback to memory cache
            return memory_cache.get(key)
            
    except Exception as e:
        logger.error(f"❌ Error getting cached embedding: {e}")
    
    return None

def set_cached_embedding(text: str, embedding: List[float]) -> None:
    """Cache embedding with TTL"""
    try:
        key = f"embed:{text}"
        
        if redis_client:
            redis_client.setex(key, EMBEDDING_TTL, json.dumps(embedding))
        else:
            # Fallback to memory cache
            memory_cache[key] = embedding
            
        logger.info(f"✅ Cached embedding for: {text[:50]}...")
        
    except Exception as e:
        logger.error(f"❌ Error caching embedding: {e}")

def get_cached_match(embedding: List[float]) -> Optional[List[Any]]:
    """Get cached search matches for embedding"""
    try:
        # Create hash of embedding for efficient key storage
        embedding_hash = hashlib.md5(str(embedding).encode()).hexdigest()
        key = f"match:{embedding_hash}"
        
        if redis_client:
            cached = redis_client.get(key)
            if cached:
                return json.loads(cached)
        else:
            # Fallback to memory cache
            return memory_cache.get(key)
            
    except Exception as e:
        logger.error(f"❌ Error getting cached matches: {e}")
    
    return None

def set_cached_match(embedding: List[float], matches: List[Any]) -> None:
    """Cache search matches with TTL"""
    try:
        # Create hash of embedding for efficient key storage
        embedding_hash = hashlib.md5(str(embedding).encode()).hexdigest()
        key = f"match:{embedding_hash}"
        
        if redis_client:
            redis_client.setex(key, MATCH_TTL, json.dumps(matches))
        else:
            # Fallback to memory cache
            memory_cache[key] = matches
            
        logger.info(f"✅ Cached {len(matches)} matches")
        
    except Exception as e:
        logger.error(f"❌ Error caching matches: {e}")

def clear_cache() -> None:
    """Clear all cache entries (useful for debugging)"""
    try:
        if redis_client:
            # Clear all keys with our prefixes
            embed_keys = redis_client.keys("embed:*")
            match_keys = redis_client.keys("match:*")
            
            if embed_keys:
                redis_client.delete(*embed_keys)
            if match_keys:
                redis_client.delete(*match_keys)
                
            logger.info(f"✅ Cleared {len(embed_keys)} embedding keys and {len(match_keys)} match keys")
        else:
            memory_cache.clear()
            logger.info("✅ Cleared memory cache")
            
    except Exception as e:
        logger.error(f"❌ Error clearing cache: {e}")

def get_cache_stats() -> dict:
    """Get cache statistics"""
    try:
        if redis_client:
            embed_keys = len(redis_client.keys("embed:*"))
            match_keys = len(redis_client.keys("match:*"))
            info = redis_client.info()
            
            return {
                "type": "redis",
                "embedding_keys": embed_keys,
                "match_keys": match_keys,
                "memory_usage": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", "N/A")
            }
        else:
            return {
                "type": "memory",
                "total_keys": len(memory_cache),
                "embedding_keys": len([k for k in memory_cache.keys() if k.startswith("embed:")]),
                "match_keys": len([k for k in memory_cache.keys() if k.startswith("match:")])
            }
            
    except Exception as e:
        logger.error(f"❌ Error getting cache stats: {e}")
        return {"error": str(e)}