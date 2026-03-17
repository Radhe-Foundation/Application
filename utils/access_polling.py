"""
Simple Access Polling - Real-time access sync without external services
Works by polling database for changes every few seconds
"""

import json
import os
import threading
import time
from datetime import datetime
from typing import Dict, Callable, Optional, List

# Global polling state
_polling_active = False
_polling_thread = None
_access_listeners: List[Callable] = []
_last_check_time = None
CHECK_INTERVAL = 5  # seconds between checks


def start_access_polling(user_id: int, on_change: Callable):
    """
    Start polling for access changes.
    Args:
        user_id: The user ID to monitor
        on_change: Callback function called when access changes detected
    """
    global _polling_active, _polling_thread, _access_listeners

    if _polling_active:
        return

    _access_listeners.append(on_change)
    _polling_active = True

    def poll_loop():
        from utils.screen_access import get_user_screen_access, get_user_button_access

        last_screen_access = get_user_screen_access(user_id)
        last_button_access = get_user_button_access(user_id)

        while _polling_active:
            time.sleep(CHECK_INTERVAL)

            if not _polling_active:
                break

            # Check for changes
            current_screen = get_user_screen_access(user_id)
            current_button = get_user_button_access(user_id)

            # Compare
            if current_screen != last_screen_access or current_button != last_button_access:
                last_screen_access = current_screen
                last_button_access = current_button

                # Notify listeners
                for listener in _access_listeners:
                    try:
                        listener({
                            'screen_access': current_screen,
                            'button_access': current_button
                        })
                    except Exception as e:
                        print(f"Access listener error: {e}")

    _polling_thread = threading.Thread(target=poll_loop, daemon=True)
    _polling_thread.start()
    print(f"Started access polling for user (interval: {CHECK_INTERVAL}s)")


def stop_access_polling():
    """Stop the polling"""
    global _polling_active, _polling_thread
    _polling_active = False
    if _polling_thread:
        _polling_thread.join(timeout=2)
    _access_listeners.clear()
    print("Stopped access polling")


def is_polling_active() -> bool:
    """Check if polling is active"""
    return _polling_active


# Alternative: Simple file-based notification (for same-machine multi-user)

ACCESS_FILE = "/tmp/RadheFoundation_access_change.json"


def notify_access_change(user_id: int, access_data: Dict):
    """
    Write access change to a temp file - other instances can read this
    """
    data = {
        'user_id': user_id,
        'timestamp': datetime.now().isoformat(),
        'access': access_data
    }
    try:
        with open(ACCESS_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error writing access notification: {e}")


def check_for_access_change(user_id: int) -> Optional[Dict]:
    """
    Check if access has been updated (for same machine)
    Returns access data if changed, None otherwise
    """
    if not os.path.exists(ACCESS_FILE):
        return None

    try:
        with open(ACCESS_FILE, 'r') as f:
            data = json.load(f)

        if data.get('user_id') == user_id:
            return data.get('access')
    except Exception as e:
        print(f"Error reading access notification: {e}")

    return None


# Usage example in screens:
"""
# In employee dashboard __init__:
from utils.access_polling import start_access_polling, stop_access_polling

def on_access_change(new_access):
    # Refresh the UI when access changes
    self.refresh_dashboard()

# Start polling when screen loads
start_access_polling(user_id, on_access_change)

# Stop when leaving screen
stop_access_polling()
"""
