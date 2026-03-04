"""
Vernika HRA - Main Entry Point
Fixed version with proper session management and performance optimizations
"""
from utils.notification_manager import init_notification_manager
from core.keyboard_shortcuts_v2 import init_keyboard_shortcuts
import flet as ft
import logging
from config import APP_NAME, APP_VERSION, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT, WINDOW_RESIZABLE, WINDOW_MAXIMIZED

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import keyboard shortcuts and notification manager


def init_db():
    """Initialize database on startup"""
    try:
        # Import from new session manager
        from database.session_manager import get_engine, init_db as create_tables
        from database.models import init_database

        # Create all tables
        create_tables()

        # Initialize default data
        init_database()
        logger.info("✓ Database initialized successfully!")

        return True
    except Exception as e:
        logger.error(f"✗ Database initialization error: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_database_health():
    """Check database health on startup"""
    try:
        from database.session_manager import get_db_health, check_db_connection

        if check_db_connection():
            health = get_db_health()
            logger.info(
                f"✓ Database connected! Response time: {health.get('response_time_ms', 0)}ms")
            return True
        else:
            logger.error("✗ Database connection failed!")
            return False
    except Exception as e:
        logger.error(f"✗ Database health check failed: {e}")
        return False


def main(page: ft.Page):
    try:
        page.title = f"{APP_NAME} v{APP_VERSION}"

        # Responsive window settings - maximize to fill screen
        page.window.min_width = WINDOW_MIN_WIDTH
        page.window.min_height = WINDOW_MIN_HEIGHT
        page.window.resizable = WINDOW_RESIZABLE
        page.window.maximized = WINDOW_MAXIMIZED

        page.fonts = {
            "Roboto": "https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap"
        }

        # Handle lifecycle events for connection monitoring
        def on_app_lifecycle_change(e):
            logger.info(f"App lifecycle state changed to: {e.state}")

        page.on_app_lifecycle_state_change = on_app_lifecycle_change

        # Check database health first
        if not check_database_health():
            page.add(ft.Column([
                ft.Icon(ft.Icons.WARNING, size=48, color=ft.Colors.RED),
                ft.Text("Database Connection Error",
                        size=24, color=ft.Colors.RED),
                ft.Text(
                    "Failed to connect to database. Please check your internet connection.", size=14),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20))
            return

        # Initialize database
        db_initialized = init_db()

        if not db_initialized:
            # Show error and exit
            page.add(ft.Column([
                ft.Text("Database Error", size=24, color=ft.Colors.RED),
                ft.Text(
                    "Failed to initialize database. Please restart the application."),
            ]))
            return

# Initialize navigation manager
        from core.navigation_v2 import init_navigation
        init_navigation(page)

        # Initialize keyboard shortcuts manager for global keyboard handling
        try:
            from core.keyboard_shortcuts_v2 import init_keyboard_shortcuts
            init_keyboard_shortcuts(page)
            logger.info("✓ Keyboard shortcuts initialized")
        except Exception as e:
            logger.warning(f"Keyboard shortcuts initialization failed: {e}")

        # Initialize notification manager
        try:
            from utils.notification_manager import init_notification_manager
            init_notification_manager(page)
            logger.info("✓ Notification manager initialized")
        except Exception as e:
            logger.warning(f"Notification manager initialization failed: {e}")

        # Show login screen
        from screens.login_screen import LoginScreen
        login_screen = LoginScreen(page)
        page.add(login_screen)

        logger.info("✓ Application started successfully")

    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    try:
        ft.run(main)
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application crashed: {e}")
        raise
