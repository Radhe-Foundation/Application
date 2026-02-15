"""
Access Sync Helper - Simple polling-free sync for multi-user access control
This module provides functions to sync access permissions without Supabase Pro realtime
"""

import time
from datetime import datetime
from typing import Dict, Optional

# In-memory cache with timestamp for access data
_access_cache: Dict[int, Dict] = {}
_cache_timeout = 30  # seconds - cache validity


def _get_cached_access(user_id: int) -> Optional[Dict]:
    """Get cached access if still valid"""
    if user_id in _access_cache:
        cached = _access_cache[user_id]
        if time.time() - cached.get('_timestamp', 0) < _cache_timeout:
            return cached
    return None


def _set_cached_access(user_id: int, access_data: Dict):
    """Cache access data with timestamp"""
    access_data['_timestamp'] = time.time()
    _access_cache[user_id] = access_data


def invalidate_access_cache(user_id: int = None):
    """Invalidate access cache - call this after admin changes permissions"""
    if user_id and user_id in _access_cache:
        del _access_cache[user_id]
    elif user_id is None:
        # Clear all cache
        _access_cache.clear()


def get_user_screen_access_cached(user_id: int) -> Dict[str, bool]:
    """
    Get screen access with caching for performance.
    Use this for employee screens - fetches from DB only when cache expires.
    Call invalidate_access_cache() after admin changes permissions.
    """
    # Check cache first
    cached = _get_cached_access(user_id)
    if cached and 'screen_access' in cached:
        return cached['screen_access']

    # Fetch from database
    from utils.screen_access import get_user_screen_access
    access = get_user_screen_access(user_id)

    # Update cache
    _set_cached_access(user_id, {'screen_access': access})

    return access


def get_user_button_access_cached(user_id: int) -> Dict[str, bool]:
    """
    Get button access with caching for performance.
    Use this for employee screens.
    """
    # Check cache first
    cached = _get_cached_access(user_id)
    if cached and 'button_access' in cached:
        return cached['button_access']

    # Fetch from database
    from utils.screen_access import get_user_button_access
    access = get_user_button_access(user_id)

    # Update cache
    existing = cached or {}
    existing['button_access'] = access
    _set_cached_access(user_id, existing)

    return access


def check_access(user_id: int, screen_key: str) -> bool:
    """Check if user has access to a screen - uses cache"""
    access = get_user_screen_access_cached(user_id)
    return access.get(screen_key, False)


def check_button_access(user_id: int, button_key: str) -> bool:
    """Check if user has access to a button - uses cache"""
    access = get_user_button_access_cached(user_id)
    return access.get(button_key, False)


def get_allowed_screens(user_id: int) -> list:
    """Get list of screens user has access to"""
    access = get_user_screen_access_cached(user_id)
    return [k for k, v in access.items() if v]


def get_allowed_buttons(user_id: int, screen: str = None) -> list:
    """Get list of buttons user has access to, optionally filtered by screen"""
    from utils.screen_access import BUTTON_ACCESS_CONFIG

    access = get_user_button_access_cached(user_id)
    allowed = [k for k, v in access.items() if v]

    if screen:
        # Filter by screen
        return [k for k in allowed if BUTTON_ACCESS_CONFIG.get(k, {}).get('screen') == screen]

    return allowed
