"""
Vernika HRA - Main Entry Point
Fixed version with proper initialization
"""
import flet as ft
import logging
from config import APP_NAME, APP_VERSION, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT, WINDOW_RESIZABLE, WINDOW_MAXIMIZED

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize database before importing screens


def init_db():
    """Initialize database on startup"""
    try:
        from database.connection import get_engine, Base
        from database.models import init_database
        # Create all tables
        Base.metadata.create_all(bind=get_engine())
        # Initialize default data
        init_database()
        logger.info("✓ Database initialized successfully!")
        # Run user-employee sync to ensure all data is properly linked
        try:
            from fix_user_employee_sync import sync_user_employee
            sync_user_employee()
        except Exception as e:
            logger.warning(f"⚠ User-employee sync failed (optional): {e}")
        return True
    except Exception as e:
        logger.error(f"✗ Database initialization error: {e}")
        return False


def main(page: ft.Page):
    try:
        page.title = f"{APP_NAME} v{APP_VERSION}"

        # Responsive window settings - maximize to fill screen
        page.window.min_width = WINDOW_MIN_WIDTH
        page.window.min_height = WINDOW_MIN_HEIGHT
        page.window.resizable = WINDOW_RESIZABLE
        page.window.maximized = WINDOW_MAXIMIZED  # Always start maximized
        page.fonts = {
            "Roboto": "https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap"}

        # Handle lifecycle events for connection monitoring
        def on_app_lifecycle_change(e):
            logger.info(f"App lifecycle state changed to: {e.state}")

        page.on_app_lifecycle_state_change = on_app_lifecycle_change

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

        from screens.login_screen import LoginScreen
        login_screen = LoginScreen(page)
        page.add(login_screen)
        logger.info("Application started successfully")

    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        raise


if __name__ == "__main__":
    try:
        ft.app(target=main, view=ft.AppView.FLET_APP)
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application crashed: {e}")
        raise
