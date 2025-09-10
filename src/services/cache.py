import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional, TypeVar, Callable, Awaitable

import aiofiles

from ..models.pokemon import Pokemon, MoveDetails

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CacheEntry:
    """Represents a cached entry with timestamp and data"""
    
    def __init__(self, data: Any, ttl_seconds: int = 3600):
        self.data = data
        self.timestamp = time.time()
        self.ttl_seconds = ttl_seconds
        
    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return time.time() - self.timestamp > self.ttl_seconds
    
    def to_dict(self) -> Dict:
        """Convert cache entry to dictionary for serialization"""
        return {
            "data": self.data,
            "timestamp": self.timestamp,
            "ttl_seconds": self.ttl_seconds
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "CacheEntry":
        """Create cache entry from dictionary"""
        entry = cls(
            data=data["data"],
            ttl_seconds=data.get("ttl_seconds", 3600)
        )
        entry.timestamp = data["timestamp"]
        return entry


class InMemoryCache:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self, default_ttl: int = 3600):
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        async with self._lock:
            if key not in self._cache:
                return None
                
            entry = self._cache[key]
            if entry.is_expired:
                del self._cache[key]
                return None
                
            return entry.data
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        async with self._lock:
            ttl = ttl or self.default_ttl
            self._cache[key] = CacheEntry(value, ttl)
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def clear(self) -> None:
        """Clear all cache entries"""
        async with self._lock:
            self._cache.clear()
    
    async def size(self) -> int:
        """Get cache size"""
        async with self._lock:
            return len(self._cache)
    
    async def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed"""
        async with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired
            ]
            
            for key in expired_keys:
                del self._cache[key]
                
            return len(expired_keys)


class FileCache:
    """File-based cache for persistent storage"""
    
    def __init__(self, cache_dir: str = ".cache", default_ttl: int = 3600):
        self.cache_dir = Path(cache_dir)
        self.default_ttl = default_ttl
        self._lock = asyncio.Lock()
        
        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_path(self, key: str) -> Path:
        """Get file path for cache key"""
        # Replace invalid filename characters
        safe_key = key.replace("/", "_").replace(":", "_").replace("?", "_")
        return self.cache_dir / f"{safe_key}.json"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from file cache"""
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            return None
        
        try:
            async with aiofiles.open(cache_path, 'r') as f:
                data = json.loads(await f.read())
                
            entry = CacheEntry.from_dict(data)
            
            if entry.is_expired:
                # Remove expired file
                try:
                    cache_path.unlink()
                except OSError:
                    pass
                return None
                
            return entry.data
            
        except (json.JSONDecodeError, KeyError, OSError) as e:
            logger.warning(f"Failed to read cache file {cache_path}: {e}")
            # Remove corrupted file
            try:
                cache_path.unlink()
            except OSError:
                pass
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in file cache"""
        async with self._lock:
            cache_path = self._get_cache_path(key)
            ttl = ttl or self.default_ttl
            
            entry = CacheEntry(value, ttl)
            
            try:
                async with aiofiles.open(cache_path, 'w') as f:
                    await f.write(json.dumps(entry.to_dict(), indent=2))
            except (OSError, json.JSONEncodeError) as e:
                logger.warning(f"Failed to write cache file {cache_path}: {e}")
    
    async def delete(self, key: str) -> bool:
        """Delete key from file cache"""
        cache_path = self._get_cache_path(key)
        
        if cache_path.exists():
            try:
                cache_path.unlink()
                return True
            except OSError as e:
                logger.warning(f"Failed to delete cache file {cache_path}: {e}")
        
        return False
    
    async def clear(self) -> None:
        """Clear all cache files"""
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
            except OSError as e:
                logger.warning(f"Failed to delete cache file {cache_file}: {e}")
    
    async def cleanup_expired(self) -> int:
        """Remove expired cache files and return count removed"""
        expired_count = 0
        
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                async with aiofiles.open(cache_file, 'r') as f:
                    data = json.loads(await f.read())
                
                entry = CacheEntry.from_dict(data)
                
                if entry.is_expired:
                    cache_file.unlink()
                    expired_count += 1
                    
            except (json.JSONDecodeError, KeyError, OSError):
                # Remove corrupted file
                try:
                    cache_file.unlink()
                    expired_count += 1
                except OSError:
                    pass
        
        return expired_count


class HybridCache:
    """Hybrid cache using both memory and file storage"""
    
    def __init__(
        self,
        cache_dir: str = ".cache",
        memory_ttl: int = 300,  # 5 minutes
        file_ttl: int = 3600,   # 1 hour
        max_memory_size: int = 100
    ):
        self.memory_cache = InMemoryCache(memory_ttl)
        self.file_cache = FileCache(cache_dir, file_ttl)
        self.memory_ttl = memory_ttl
        self.file_ttl = file_ttl
        self.max_memory_size = max_memory_size
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from hybrid cache (memory first, then file)"""
        # Try memory cache first
        value = await self.memory_cache.get(key)
        if value is not None:
            return value
        
        # Try file cache
        value = await self.file_cache.get(key)
        if value is not None:
            # Store in memory for faster future access
            await self.memory_cache.set(key, value, self.memory_ttl)
            return value
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in both memory and file cache"""
        # Manage memory cache size
        if await self.memory_cache.size() >= self.max_memory_size:
            await self.memory_cache.cleanup_expired()
        
        await asyncio.gather(
            self.memory_cache.set(key, value, self.memory_ttl),
            self.file_cache.set(key, value, ttl or self.file_ttl)
        )
    
    async def delete(self, key: str) -> bool:
        """Delete key from both caches"""
        memory_deleted, file_deleted = await asyncio.gather(
            self.memory_cache.delete(key),
            self.file_cache.delete(key)
        )
        return memory_deleted or file_deleted
    
    async def clear(self) -> None:
        """Clear both caches"""
        await asyncio.gather(
            self.memory_cache.clear(),
            self.file_cache.clear()
        )
    
    async def cleanup_expired(self) -> Dict[str, int]:
        """Cleanup expired entries in both caches"""
        memory_expired, file_expired = await asyncio.gather(
            self.memory_cache.cleanup_expired(),
            self.file_cache.cleanup_expired()
        )
        
        return {
            "memory": memory_expired,
            "file": file_expired
        }


class CachedPokeAPIClient:
    """Wrapper around PokeAPIClient with caching capabilities"""
    
    def __init__(self, cache: Optional[HybridCache] = None):
        self.cache = cache or HybridCache()
    
    async def cached_fetch(
        self,
        key: str,
        fetch_func: Callable[[], Awaitable[T]],
        ttl: Optional[int] = None
    ) -> T:
        """Generic cached fetch function"""
        # Try cache first
        cached_value = await self.cache.get(key)
        if cached_value is not None:
            logger.debug(f"Cache hit for key: {key}")
            return cached_value
        
        # Fetch from API
        logger.debug(f"Cache miss for key: {key}, fetching from API")
        value = await fetch_func()
        
        # Store in cache
        await self.cache.set(key, value, ttl)
        
        return value
    
    def _pokemon_cache_key(self, identifier: str) -> str:
        """Generate cache key for pokemon data"""
        return f"pokemon:{identifier}"
    
    def _move_cache_key(self, identifier: str) -> str:
        """Generate cache key for move data"""
        return f"move:{identifier}"
    
    def _type_effectiveness_cache_key(self, type_name: str) -> str:
        """Generate cache key for type effectiveness"""
        return f"type_effectiveness:{type_name}"
    
    async def get_pokemon(self, client, identifier: str) -> Pokemon:
        """Get Pokemon with caching"""
        cache_key = self._pokemon_cache_key(identifier)
        
        async def fetch():
            return await client.get_pokemon(identifier)
        
        # Cache for 1 hour (Pokemon data doesn't change frequently)
        result = await self.cached_fetch(cache_key, fetch, ttl=3600)
        
        # Convert dict back to Pokemon model if needed
        if isinstance(result, dict):
            result = Pokemon(**result)
        
        return result
    
    async def get_move_details(self, client, move_identifier: str) -> MoveDetails:
        """Get move details with caching"""
        cache_key = self._move_cache_key(move_identifier)
        
        async def fetch():
            return await client.get_move_details(move_identifier)
        
        result = await self.cached_fetch(cache_key, fetch, ttl=3600)
        
        if isinstance(result, dict):
            result = MoveDetails(**result)
        
        return result
    
    async def get_type_effectiveness(self, client, type_name: str) -> Dict[str, float]:
        """Get type effectiveness with caching"""
        cache_key = self._type_effectiveness_cache_key(type_name)
        
        async def fetch():
            return await client.get_type_effectiveness(type_name)
        
        # Cache for 24 hours (type effectiveness is static)
        return await self.cached_fetch(cache_key, fetch, ttl=86400)
    
    async def cleanup(self) -> Dict[str, int]:
        """Cleanup expired cache entries"""
        return await self.cache.cleanup_expired()


# Global cache instance
_global_cache: Optional[HybridCache] = None


def get_global_cache() -> HybridCache:
    """Get or create global cache instance"""
    global _global_cache
    if _global_cache is None:
        cache_dir = os.getenv("POKEMON_CACHE_DIR", ".cache")
        _global_cache = HybridCache(cache_dir=cache_dir)
    return _global_cache


async def cleanup_global_cache() -> Dict[str, int]:
    """Cleanup global cache"""
    cache = get_global_cache()
    return await cache.cleanup()