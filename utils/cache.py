"""
RadheFoundation HRA - Performance Cache Module
Provides in-memory caching for frequently accessed data
"""

import time
import threading
from typing import Any, Optional, Callable
from functools import wraps


class CacheEntry:
    """Cache entry with expiration"""

    def __init__(self, value: Any, ttl: int = 60):
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl  # Time to live in seconds

    def is_expired(self) -> bool:
        return time.time() - self.created_at > self.ttl


class PerformanceCache:
    """
    Thread-safe in-memory cache for application data.
    Reduces database load by caching frequently accessed data.
    """

    def __init__(self):
        self._cache: dict[str, CacheEntry] = {}
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        with self._lock:
            entry = self._cache.get(key)
            if entry and not entry.is_expired():
                return entry.value
            elif entry:
                # Remove expired entry
                del self._cache[key]
            return None

    def set(self, key: str, value: Any, ttl: int = 60):
        """Set value in cache with TTL"""
        with self._lock:
            self._cache[key] = CacheEntry(value, ttl)

    def delete(self, key: str):
        """Delete specific key from cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]

    def clear(self):
        """Clear all cache"""
        with self._lock:
            self._cache.clear()

    def invalidate_prefix(self, prefix: str):
        """Invalidate all keys starting with prefix"""
        with self._lock:
            keys_to_delete = [
                k for k in self._cache.keys() if k.startswith(prefix)]
            for key in keys_to_delete:
                del self._cache[key]

    def get_stats(self) -> dict:
        """Get cache statistics"""
        with self._lock:
            total = len(self._cache)
            expired = sum(1 for e in self._cache.values() if e.is_expired())
            return {
                'total_entries': total,
                'expired_entries': expired,
                'active_entries': total - expired
            }


# Global cache instance
_cache = PerformanceCache()


# Cache keys
class CacheKeys:
    """Constants for cache keys"""
    # Dashboard
    DASHBOARD_STATS = "dashboard:stats"

    # Employees
    ALL_EMPLOYEES = "employees:all"
    EMPLOYEE_BY_ID = "employees:id:"
    EMPLOYEES_BY_DEPT = "employees:dept:"

    # Departments
    ALL_DEPARTMENTS = "departments:all"

    # Tasks
    ALL_TASKS = "tasks:all"
    PENDING_TASKS = "tasks:pending"

    # Users
    ALL_USERS = "users:all"


def cached(key: str, ttl: int = 60):
    """
    Decorator to cache function results.

    Usage:
        @cached("mykey", ttl=30)
        def get_data():
            return expensive_operation()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Try to get from cache
            cached_value = _cache.get(key)
            if cached_value is not None:
                return cached_value

            # Compute and cache
            result = func(*args, **kwargs)
            _cache.set(key, result, ttl)
            return result
        return wrapper
    return decorator


def get_cache() -> PerformanceCache:
    """Get the global cache instance"""
    return _cache


def invalidate_cache(prefix: str = ""):
    """Invalidate cache entries"""
    if prefix:
        _cache.invalidate_prefix(prefix)
    else:
        _cache.clear()


# Convenience functions with built-in caching

def get_cached_dashboard_stats(force_refresh: bool = False) -> dict:
    """
    Get dashboard statistics with caching.
    Cache expires after 30 seconds.
    """
    if not force_refresh:
        cached = _cache.get(CacheKeys.DASHBOARD_STATS)
        if cached:
            return cached

    # Get fresh data
    from sqlalchemy import func
    from database.session_manager import get_session
    from database.models import Employee, Attendance, LeaveRequest, Task
    from database.models import AttendanceStatus, LeaveStatus, TaskStatus
    from datetime import datetime

    stats = {
        'total_employees': 0,
        'present_today': 0,
        'on_leave': 0,
        'pending_tasks': 0,
    }

    try:
        with get_session() as session:
            today = datetime.now().date()

            # Single optimized query for all counts
            stats['total_employees'] = session.query(func.count(Employee.id)).filter(
                Employee.is_active == True
            ).scalar() or 0

            stats['present_today'] = session.query(func.count(Attendance.id)).filter(
                Attendance.date == today,
                Attendance.status == AttendanceStatus.PRESENT
            ).scalar() or 0

            stats['on_leave'] = session.query(func.count(LeaveRequest.id)).filter(
                LeaveRequest.status == LeaveStatus.APPROVED,
                LeaveRequest.start_date <= today,
                LeaveRequest.end_date >= today
            ).scalar() or 0

            stats['pending_tasks'] = session.query(func.count(Task.id)).filter(
                Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS])
            ).scalar() or 0

        # Cache the result
        _cache.set(CacheKeys.DASHBOARD_STATS, stats, ttl=30)

    except Exception as e:
        print(f"Error getting dashboard stats: {e}")

    return stats


def invalidate_dashboard_cache():
    """Invalidate dashboard cache"""
    _cache.delete(CacheKeys.DASHBOARD_STATS)


# ============================================
# Global cache instance for app-wide use
# ============================================
# Global cache instance
_global_cache = PerformanceCache()


def get_global_cache() -> PerformanceCache:
    """Get the global cache instance"""
    return _global_cache


def cache_screen_data(screen_name: str, data: Any, ttl: int = 30):
    """
    Cache screen data to avoid re-fetching from DB on every visit.
    TTL is 30 seconds by default - balances freshness with performance.
    """
    key = f"screen_{screen_name}"
    _global_cache.set(key, data, ttl)


def get_cached_screen_data(screen_name: str) -> Optional[Any]:
    """Get cached screen data if available"""
    key = f"screen_{screen_name}"
    return _global_cache.get(key)


def cache_user_data(user_id: int, data: Any, ttl: int = 60):
    """Cache user-specific data"""
    key = f"user_{user_id}"
    _global_cache.set(key, data, ttl)


def get_cached_user_data(user_id: int) -> Optional[Any]:
    """Get cached user data"""
    key = f"user_{user_id}"
    return _global_cache.get(key)


def invalidate_user_cache(user_id: int):
    """Clear cached data for a specific user"""
    key = f"user_{user_id}"
    _global_cache.delete(key)


def invalidate_all_cache():
    """Clear all cached data"""
    _global_cache._cache.clear()
