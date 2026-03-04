"""
Vernika HRA - Shared Navigation Utilities
Centralized navigation functions to replace duplicate code across screens
"""

import flet as ft
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from flet import Page

# Import overlay cleanup utilities
from utils.overlay_cleanup import cleanup_all_pickers, close_all_dialogs


# Navigation helper functions
def safe_navigate_to_home(page: 'Page', user: Optional[Any] = None) -> None:
    """
    Safely navigate to the appropriate home screen based on user role.
    This replaces duplicate _safe_navigate_to_home() functions in multiple screens.

    Args:
        page: Flet page object
        user: User object (dict or User model)
    """
    try:
        # Clean up overlays before navigation to prevent stale FilePicker errors
        cleanup_all_pickers(page)
        close_all_dialogs(page)

        # Get user role
        user_role = None
        if user:
            if isinstance(user, dict):
                user_role = user.get('role', 'employee').lower()
            elif hasattr(user, 'role'):
                role = user.role
                if hasattr(role, 'name'):
                    user_role = role.name.lower()
                else:
                    user_role = str(role).lower()
            else:
                user_role = 'employee'
        else:
            user_role = 'employee'

        # Import here to avoid circular imports
        from screens.admin_screen import AdminScreen
        from screens.employee_screen import EmployeeScreen

        page.clean()

        if user_role == 'admin':
            page.add(AdminScreen(page, user))
        else:
            page.add(EmployeeScreen(page, user))

    except Exception as e:
        print(f"Navigation error: {e}")
        # Fallback to login screen
        try:
            from screens.login_screen import LoginScreen
            page.clean()
            page.add(LoginScreen(page))
        except Exception as fallback_error:
            print(f"Fallback navigation failed: {fallback_error}")


def navigate_to_login(page: 'Page') -> None:
    """Navigate to login screen"""
    try:
        # Clean up overlays before navigation to prevent stale FilePicker errors
        cleanup_all_pickers(page)
        close_all_dialogs(page)

        from screens.login_screen import LoginScreen
        page.clean()
        page.add(LoginScreen(page))
    except Exception as e:
        print(f"Navigate to login error: {e}")


def navigate_to_admin(page: 'Page', user: Any) -> None:
    """Navigate to admin screen"""
    try:
        # Clean up overlays before navigation
        cleanup_all_pickers(page)
        close_all_dialogs(page)

        from screens.admin_screen import AdminScreen
        page.clean()
        page.add(AdminScreen(page, user))
    except Exception as e:
        print(f"Navigate to admin error: {e}")
        show_error_snackbar(page, f"Navigation error: {str(e)}")


def navigate_to_employee(page: 'Page', user: Any) -> None:
    """Navigate to employee screen"""
    try:
        # Clean up overlays before navigation
        cleanup_all_pickers(page)
        close_all_dialogs(page)

        from screens.employee_screen import EmployeeScreen
        page.clean()
        page.add(EmployeeScreen(page, user))
    except Exception as e:
        print(f"Navigate to employee error: {e}")
        show_error_snackbar(page, f"Navigation error: {str(e)}")


def navigate_to_screen(page: 'Page', screen_name: str, user: Any = None, **kwargs) -> None:
    """
    Navigate to a specific screen by name.

    Args:
        page: Flet page object
        screen_name: Name of the screen ('dashboard', 'employees', 'attendance', etc.)
        user: Current user object
        **kwargs: Additional parameters to pass to the screen
    """
    # Clean up overlays before navigation to prevent stale FilePicker errors
    cleanup_all_pickers(page)
    close_all_dialogs(page)

    screen_map = {
        'dashboard': ('screens.dashboard_screen', 'DashboardScreen'),
        'employees': ('screens.employees_screen', 'EmployeesScreen'),
        'employee': ('screens.employee_screen', 'EmployeeScreen'),
        'admin': ('screens.admin_screen', 'AdminScreen'),
        'login': ('screens.login_screen', 'LoginScreen'),
        'attendance': ('screens.attendance_screen', 'AttendanceScreen'),
        'leaves': ('screens.leaves_screen', 'LeavesScreen'),
        'tasks': ('screens.tasks_screen', 'TasksScreen'),
        'departments': ('screens.departments_screen', 'DepartmentsScreen'),
        'positions': ('screens.positions_screen', 'PositionsScreen'),
        'teams': ('screens.teams_screen', 'TeamsScreen'),
        'projects': ('screens.projects_screen', 'ProjectsScreen'),
        'holidays': ('screens.holidays_screen', 'HolidaysScreen'),
        'meetings': ('screens.meetings_screen', 'MeetingsScreen'),
        'announcements': ('screens.announcements_screen', 'AnnouncementsScreen'),
        'settings': ('screens.settings_screen', 'SettingsScreen'),
        'chat': ('screens.chat_screen', 'ChatScreen'),
        'mail': ('screens.mail_screen', 'MailScreen'),
        'todo': ('screens.todo_screen', 'TodoScreen'),
        'profile': ('screens.profile_screen', 'ProfileScreen'),
        'inventory': ('screens.inventory_screen', 'InventoryScreen'),
        'transactions': ('screens.transactions_screen', 'TransactionsScreen'),
        'time_tracking': ('screens.time_tracking_screen', 'TimeTrackingScreen'),
        'org_tree': ('screens.organization_tree_screen', 'OrganizationTreeScreen'),
        'data_entry': ('screens.data_entry_screen', 'DataEntryScreen'),
    }

    if screen_name.lower() not in screen_map:
        print(f"Unknown screen: {screen_name}")
        safe_navigate_to_home(page, user)
        return

    try:
        module_path, class_name = screen_map[screen_name.lower()]

        # Dynamic import
        import importlib
        module = importlib.import_module(module_path)
        screen_class = getattr(module, class_name)

        page.clean()

        # Handle screens with different constructor signatures
        if screen_name.lower() in ['admin', 'login']:
            page.add(screen_class(
                page, user if screen_name.lower() != 'login' else None))
        elif screen_name.lower() == 'employees':
            page.add(screen_class(page, user))
        else:
            # Try with page and user, fallback to just page
            try:
                page.add(screen_class(page, user))
            except TypeError:
                try:
                    page.add(screen_class(page))
                except TypeError:
                    page.add(screen_class())

    except Exception as e:
        print(f"Navigate to {screen_name} error: {e}")
        import traceback
        traceback.print_exc()
        safe_navigate_to_home(page, user)


# UI Helper functions
def show_success_snackbar(page: 'Page', message: str) -> None:
    """Show a success snackbar message"""
    try:
        snack = ft.SnackBar(
            content=ft.Text(message),
            bgcolor="#4CAF50"  # Green
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()
    except Exception as e:
        print(f"Snackbar error: {e}")


def show_error_snackbar(page: 'Page', message: str) -> None:
    """Show an error snackbar message"""
    try:
        snack = ft.SnackBar(
            content=ft.Text(message),
            bgcolor="#F44336"  # Red
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()
    except Exception as e:
        print(f"Snackbar error: {e}")


def show_info_snackbar(page: 'Page', message: str) -> None:
    """Show an info snackbar message"""
    try:
        snack = ft.SnackBar(
            content=ft.Text(message),
            bgcolor="#2196F3"  # Blue
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()
    except Exception as e:
        print(f"Snackbar error: {e}")


def show_warning_snackbar(page: 'Page', message: str) -> None:
    """Show a warning snackbar message"""
    try:
        snack = ft.SnackBar(
            content=ft.Text(message),
            bgcolor="#FF9800"  # Orange
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()
    except Exception as e:
        print(f"Snackbar error: {e}")


# Dialog helper functions
def close_all_dialogs(page: 'Page') -> None:
    """Close all open dialogs"""
    try:
        for overlay in page.overlay:
            if isinstance(overlay, ft.AlertDialog) and overlay.open:
                overlay.open = False
        page.update()
    except Exception as e:
        print(f"Close dialogs error: {e}")


def show_confirm_dialog(
    page: 'Page',
    title: str,
    content: str,
    on_confirm: callable,
    confirm_text: str = "Confirm",
    cancel_text: str = "Cancel",
    confirm_color: str = "#F44336"
) -> None:
    """Show a confirmation dialog"""
    def close_dlg(e):
        close_all_dialogs(page)

    def handle_confirm(e):
        on_confirm(e)
        close_all_dialogs(page)

    dialog = ft.AlertDialog(
        title=ft.Text(title),
        content=ft.Text(content),
        actions=[
            ft.TextButton(cancel_text, on_click=close_dlg),
            ft.ElevatedButton(
                confirm_text,
                on_click=handle_confirm,
                style=ft.ButtonStyle(bgcolor=confirm_color, color="WHITE")
            )
        ],
        actions_alignment=ft.MainAxisAlignment.END
    )

    page.overlay.append(dialog)
    dialog.open = True
    page.update()


def show_loading(page: 'Page', message: str = "Loading...") -> ft.ProgressRing:
    """Show loading indicator"""
    loading = ft.ProgressRing(width=20, height=20, visible=True)
    return loading


# Date/Time helpers
def parse_date(date_str: str) -> Optional[Any]:
    """Parse date string to date object"""
    from datetime import datetime, date

    if not date_str:
        return None

    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%m-%d-%Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except (ValueError, TypeError):
            continue

    print(f"Warning: Could not parse date: {date_str}")
    return None


def format_date(date_obj: Any, format_str: str = "%Y-%m-%d") -> str:
    """Format date object to string"""
    if not date_obj:
        return "-"

    try:
        return date_obj.strftime(format_str)
    except Exception:
        return str(date_obj)


def get_date_range(start_date: Any, end_date: Any) -> int:
    """Calculate number of days between two dates"""
    if not start_date or not end_date:
        return 0

    try:
        from datetime import timedelta
        return (end_date - start_date).days + 1  # Include both start and end
    except Exception:
        return 0


# Validation helpers
def validate_email(email: str) -> bool:
    """Validate email format"""
    import re
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    import re
    if not phone:
        return False
    # Allow various phone formats
    pattern = r'^[+]?[\d\s\-()]{7,20}$'
    return bool(re.match(pattern, phone))


def validate_required(value: Any, field_name: str = "Field") -> tuple:
    """
    Validate that a required field has a value.
    Returns (is_valid, error_message)
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        return False, f"{field_name} is required"
    return True, ""


# Safe property access
def safe_get(obj: Any, attr: str, default: Any = None) -> Any:
    """Safely get attribute from object"""
    try:
        return getattr(obj, attr, default)
    except Exception:
        return default


def safe_get_dict(data: Dict, key: str, default: Any = None) -> Any:
    """Safely get value from dictionary"""
    try:
        return data.get(key, default)
    except Exception:
        return default


# Color constants for consistent UI
class Colors:
    """Application color constants"""
    PRIMARY = "#2E86AB"
    PRIMARY_DARK = "#1A5F7A"
    PRIMARY_LIGHT = "#4DA8DA"

    SECONDARY = "#A23B72"
    SECONDARY_DARK = "#7A2A55"
    SECONDARY_LIGHT = "#C75B9A"

    SUCCESS = "#28A745"
    SUCCESS_LIGHT = "#4CAF50"

    ERROR = "#DC3545"
    ERROR_LIGHT = "#F44336"

    WARNING = "#FFC107"
    WARNING_LIGHT = "#FF9800"

    INFO = "#17A2B8"
    INFO_LIGHT = "#2196F3"

    BACKGROUND = "#F8F9FA"
    SURFACE = "#FFFFFF"
    SURFACE_VARIANT = "#E8E8E8"

    TEXT_PRIMARY = "#212529"
    TEXT_SECONDARY = "#6C757D"
    TEXT_DISABLED = "#ADB5BD"

    # Status colors
    ACTIVE = "#4CAF50"
    INACTIVE = "#9E9E9E"
    PENDING = "#FFC107"
    APPROVED = "#4CAF50"
    REJECTED = "#F44336"

    # Priority colors
    PRIORITY_LOW = "#4CAF50"
    PRIORITY_MEDIUM = "#FFC107"
    PRIORITY_HIGH = "#FF9800"
    PRIORITY_URGENT = "#F44336"


# Export functions
def export_to_csv(data: list, filename: str, headers: list = None) -> str:
    """
    Export data to CSV file.

    Args:
        data: List of dictionaries or objects
        filename: Output filename
        headers: Optional list of column headers

    Returns:
        Path to saved file
    """
    import csv
    import os
    from datetime import datetime

    # Create reports directory
    output_dir = "reports"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename}_{timestamp}.csv"
    filepath = os.path.join(output_dir, filename)

    if not data:
        # Create empty file with headers
        with open(filepath, 'w', newline='') as f:
            if headers:
                writer = csv.writer(f)
                writer.writerow(headers)
        return filepath

    # Determine headers from first record if not provided
    if not headers:
        if isinstance(data[0], dict):
            headers = list(data[0].keys())
        else:
            # Get attributes from object
            headers = [attr for attr in dir(data[0])
                       if not attr.startswith('_') and not callable(getattr(data[0], attr))]

    # Write CSV
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)

        for row in data:
            if isinstance(row, dict):
                writer.writerow([row.get(h, '') for h in headers])
            else:
                writer.writerow([getattr(row, h, '') for h in headers])

    return filepath


def export_to_excel(data: list, filename: str, sheet_name: str = "Sheet1") -> str:
    """
    Export data to Excel file.

    Args:
        data: List of dictionaries or objects
        filename: Output filename
        sheet_name: Name of the Excel sheet

    Returns:
        Path to saved file
    """
    try:
        import pandas as pd
        import os
        from datetime import datetime

        # Create reports directory
        output_dir = "reports"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename}_{timestamp}.xlsx"
        filepath = os.path.join(output_dir, filename)

        # Convert to DataFrame
        if data:
            df = pd.DataFrame(data)
        else:
            df = pd.DataFrame()

        # Save to Excel
        df.to_excel(filepath, sheet_name=sheet_name, index=False)

        return filepath

    except ImportError:
        print("pandas not installed, falling back to CSV")
        return export_to_csv(data, filename)
    except Exception as e:
        print(f"Excel export error: {e}")
        raise


# Pagination helper
def paginate_data(data: list, page: int = 1, per_page: int = 20) -> tuple:
    """
    Paginate a list of data.

    Returns:
        (paginated_data, total_pages, total_items)
    """
    if not data:
        return [], 0, 0

    total_items = len(data)
    total_pages = (total_items + per_page - 1) // per_page

    # Ensure page is within bounds
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    return data[start_idx:end_idx], total_pages, total_items


# Currency/Number formatting
def format_currency(amount: float, currency: str = "₹") -> str:
    """Format number as currency"""
    if amount is None:
        return f"{currency}0.00"
    return f"{currency}{amount:,.2f}"


def format_number(num: float, decimals: int = 2) -> str:
    """Format number with commas"""
    if num is None:
        return "0"
    return f"{num:,.{decimals}f}"


def parse_number(value: Any) -> float:
    """Parse string to number safely"""
    if value is None:
        return 0.0

    if isinstance(value, (int, float)):
        return float(value)

    # Remove commas and spaces
    if isinstance(value, str):
        value = value.replace(',', '').replace(' ', '')
        try:
            return float(value)
        except ValueError:
            return 0.0

    return 0.0
