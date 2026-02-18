"""
Vernika HRA - Caching Utilities
In-memory cache for frequently accessed data to improve performance
"""

import time
from typing import Any, Optional, Dict
from threading import Lock


class CacheEntry:
    """Single cache entry with expiration"""

    def __init__(self, value: Any, ttl: int = 300):
        """
        Initialize cache entry

        Args:
            value: The cached value
            ttl: Time to live in seconds (default: 5 minutes)
        """
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl

    def is_expired(self) -> bool:
        """Check if the cache entry has expired"""
        return time.time() - self.created_at > self.ttl


class MemoryCache:
    """
    Thread-safe in-memory cache for application data
    """

    def __init__(self):
        """Initialize the cache"""
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self._cache:
                return None

            entry = self._cache[key]
            if entry.is_expired():
                del self._cache[key]
                return None

            return entry.value

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """
        Set a value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        with self._lock:
            self._cache[key] = CacheEntry(value, ttl)

    def delete(self, key: str) -> bool:
        """
        Delete a key from cache

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries

        Returns:
            Number of entries removed
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)

    def get_or_set(self, key: str, factory: callable, ttl: int = 300) -> Any:
        """
        Get value from cache or create it using factory function

        Args:
            key: Cache key
            factory: Function to create value if not cached
            ttl: Time to live in seconds

        Returns:
            Cached or newly created value
        """
        value = self.get(key)
        if value is None:
            value = factory()
            self.set(key, value, ttl)
        return value


# Global cache instance
_app_cache = MemoryCache()


def get_cache() -> MemoryCache:
    """Get the global cache instance"""
    return _app_cache


# Convenience functions

def cache_get(key: str) -> Optional[Any]:
    """Get value from cache"""
    return _app_cache.get(key)


def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    """Set value in cache"""
    _app_cache.set(key, value, ttl)


def cache_delete(key: str) -> bool:
    """Delete value from cache"""
    return _app_cache.delete(key)


def cache_clear() -> None:
    """Clear all cache"""
    _app_cache.clear()


# Cache keys for common data
class CacheKeys:
    """Pre-defined cache keys"""

    # User related
    USER_PREFIX = "user:"
    USER_BY_ID = "user:id:"
    USER_BY_USERNAME = "user:username:"

    # Employee related
    EMPLOYEE_PREFIX = "employee:"
    EMPLOYEE_BY_USER_ID = "employee:user_id:"
    EMPLOYEE_BY_ID = "employee:id:"

    # Department related
    DEPARTMENTS_ALL = "departments:all"
    DEPARTMENT_BY_ID = "department:id:"

    # Position related
    POSITIONS_ALL = "positions:all"
    POSITIONS_BY_DEPT = "positions:dept:"

    # Statistics
    DASHBOARD_STATS = "stats:dashboard"

    # Lists
    ACTIVE_EMPLOYEES = "employees:active"
    ALL_USERS = "users:all"


def cache_user(user_id: int, user_data: dict, ttl: int = 300) -> None:
    """Cache user data"""
    cache_set(f"{CacheKeys.USER_BY_ID}{user_id}", user_data, ttl)


def get_cached_user(user_id: int) -> Optional[dict]:
    """Get cached user data"""
    return cache_get(f"{CacheKeys.USER_BY_ID}{user_id}")


def cache_departments(departments: list, ttl: int = 600) -> None:
    """Cache all departments"""
    cache_set(CacheKeys.DEPARTMENTS_ALL, departments, ttl)


def get_cached_departments() -> Optional[list]:
    """Get cached departments"""
    return cache_get(CacheKeys.DEPARTMENTS_ALL)


def cache_positions(positions: list, ttl: int = 600) -> None:
    """Cache all positions"""
    cache_set(CacheKeys.POSITIONS_ALL, positions, ttl)


def get_cached_positions() -> Optional[list]:
    """Get cached positions"""
    return cache_get(CacheKeys.POSITIONS_ALL)


def cache_dashboard_stats(stats: dict, ttl: int = 60) -> None:
    """Cache dashboard statistics (short TTL due to frequent updates)"""
    cache_set(CacheKeys.DASHBOARD_STATS, stats, ttl)


def get_cached_dashboard_stats() -> Optional[dict]:
    """Get cached dashboard statistics"""
    return cache_get(CacheKeys.DASHBOARD_STATS)


def invalidate_user_cache(user_id: int) -> None:
    """Invalidate user-related cache"""
    cache_delete(f"{CacheKeys.USER_BY_ID}{user_id}")


def invalidate_employee_cache(user_id: int = None, employee_id: int = None) -> None:
    """Invalidate employee-related cache"""
    if user_id:
        cache_delete(f"{CacheKeys.EMPLOYEE_BY_USER_ID}{user_id}")
    if employee_id:
        cache_delete(f"{CacheKeys.EMPLOYEE_BY_ID}{employee_id}")
    # Invalidate lists that include employees
    cache_delete(CacheKeys.ACTIVE_EMPLOYEES)
    cache_delete(CacheKeys.DASHBOARD_STATS)


def invalidate_department_cache() -> None:
    """Invalidate department-related cache"""
    cache_delete(CacheKeys.DEPARTMENTS_ALL)
    cache_delete(CacheKeys.POSITIONS_ALL)
    cache_delete(CacheKeys.DASHBOARD_STATS)


def invalidate_position_cache() -> None:
    """Invalidate position-related cache"""
    cache_delete(CacheKeys.POSITIONS_ALL)
    cache_delete(CacheKeys.DASHBOARD_STATS)
