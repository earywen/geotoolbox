
import os
import logging
from typing import Optional, Any
from diskcache import Cache

# Default cache directory in user's app data
CACHE_DIR = os.path.join(os.environ.get('APPDATA', '.'), 'Geotoolbox', 'cache')

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Singleton manager for disk-based caching using `diskcache`.
    
    Attributes:
        _instance (CacheManager): Singleton instance.
        _cache (Cache): The underlying DiskCache instance.
    """
    _instance = None
    _cache = None

    import threading
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "CacheManager":
        """Returns the singleton instance of CacheManager."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def __init__(self):
        """Initializes the CacheManager and the underling DiskCache."""
        if not os.path.exists(CACHE_DIR):
            try:
                os.makedirs(CACHE_DIR)
            except OSError as e:
                logger.error(f"Failed to create cache dir {CACHE_DIR}: {e}")
        
        # Initialize DiskCache
        # Size limit: 500MB, Eviction: LRU
        try:
            self._cache = Cache(CACHE_DIR, size_limit=500 * 1024 * 1024)
            logger.info(f"Cache initialized at {CACHE_DIR} (ID: {id(self)})")
        except Exception as e:
            logger.error(f"Failed to init DiskCache: {e}")
            self._cache = None

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a value from the cache.

        Args:
            key (str): The cache key.
            default (Any, optional): Value to return if key not found.

        Returns:
            Any: The cached value or default.
        """
        if self._cache is not None:
            try:
                return self._cache.get(key, default=default)
            except Exception:
                return default
        return default

    def set(self, key: str, value: Any, expire: Optional[float] = None, tag: Optional[str] = None) -> bool:
        """
        Set a value in the cache.

        Args:
            key (str): The cache key.
            value (Any): The value to store.
            expire (float, optional): Expiration time in seconds.
            tag (str, optional): Tag for the cache item.

        Returns:
            bool: True if successful, False otherwise.
        """
        if self._cache is not None:
            try:
                self._cache.set(key, value, expire=expire, tag=tag)
                return True
            except Exception as e:
                logger.error(f"Cache SET error: {e}")
        return False

    def clear(self) -> None:
        """Clears the entire cache."""
        if self._cache is not None:
            self._cache.clear()

# Global accessor
def get_cache() -> CacheManager:
    """Helper to get the global CacheManager instance."""
    return CacheManager.get_instance()
