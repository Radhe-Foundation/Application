"""
Lightweight smoke tests to ensure all major screens can be imported.

These don't drive the full Flet UI, but they catch missing dependencies
or syntax errors early so the app is closer to production-ready.
"""

import importlib

import pytest


@pytest.mark.parametrize(
    "module_name",
    [
        "screens.login_screen",
        "screens.admin_screen",
        "screens.employee_screen",
        "screens.chat_screen",
        "screens.dashboard_screen",
        "screens.tasks_screen",
        "screens.leaves_screen",
        "screens.attendance_screen",
        "screens.documents_screen",
        "screens.announcements_screen",
        "screens.performance_screen",
        "screens.reports_screen",
        "screens.settings_screen",
        "screens.todo_screen",
        "screens.departments_screen",
        "screens.positions_screen",
        "screens.teams_screen",
        "screens.announcements_screen",
    ],
)
def test_screen_module_imports(module_name: str):
    """Each listed screen module should import without raising errors."""
    importlib.import_module(module_name)

