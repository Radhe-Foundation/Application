"""
Vernika HRA - Web Entry Point
For deployment on Deta Space / Vercel / Render
"""
import flet as ft
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main(page: ft.Page):
    try:
        from config import APP_NAME, APP_VERSION

        page.title = f"{APP_NAME} v{APP_VERSION}"

        # Responsive window settings
        page.window.min_width = 1024
        page.window.min_height = 768
        page.window.resizable = True
        page.window.maximized = True

        page.fonts = {
            "Roboto": "https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap"
        }

        # Check database health
        try:
            from database.session_manager import check_db_connection, get_db_health
            if check_db_connection():
                health = get_db_health()
                logger.info(
                    f"✓ Database connected! Response time: {health.get('response_time_ms', 0)}ms")
            else:
                page.add(ft.Column([
                    ft.Icon(ft.Icons.WARNING, size=48, color=ft.Colors.RED),
                    ft.Text("Database Connection Error",
                            size=24, color=ft.Colors.RED),
                    ft.Text(
                        "Failed to connect to database. Please check your internet connection.", size=14),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20))
                return
        except Exception as e:
            logger.warning(f"Database check skipped: {e}")

        # Initialize database
        try:
            from database.session_manager import get_engine, init_db as create_tables
            from database.models import init_database
            create_tables()
            init_database()
            logger.info("✓ Database initialized successfully!")
        except Exception as e:
            logger.warning(f"Database initialization warning: {e}")

        # Initialize navigation
        from core.navigation_v2 import init_navigation
        init_navigation(page)

        # Initialize keyboard shortcuts
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
        page.add(ft.Column([
            ft.Text("Application Error", size=24, color=ft.Colors.RED),
            ft.Text(str(e), size=14),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20))


# For Deta Space / Vercel / Render
if __name__ == "__main__":
    import sys
    port = int(os.getenv("PORT", "8080"))
    logger.info(f"Starting Vernika HRA on port {port}")
    # Use threaded mode for better compatibility
    ft.app(target=main, host="0.0.0.0", port=port, thread=True)
