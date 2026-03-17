from flet import border, padding, ButtonStyle
import flet as ft
from typing import List, Dict, Any, Optional, Callable
from flet import (
    Row,
    Column,
    Container,
    Text,
    Image,
    IconButton,
    ElevatedButton,
    ListView,
    ScrollMode,
    ProgressRing,
    BorderRadius,
    alignment,
    Colors,
    FontWeight,
    TextAlign,
    AlertDialog,
    SnackBar,
    Icon,
    TextButton,
    ButtonStyle as BtnStyle,
)

NAV_WIDTH_EXPANDED = 260
NAV_WIDTH_COLLAPSED = 64

# Color constants for consistent UI
PRIMARY_COLOR = "#2E86AB"
PRIMARY_HOVER = "#2470A0"
SUCCESS_COLOR = "#4CAF50"
WARNING_COLOR = "#FF9800"
DANGER_COLOR = "#DC3545"
INFO_COLOR = "#2196F3"


def make_logo_block(logo_image: str | None = None, company_name: str = "RadheFoundation"):
    img = Image(src=logo_image, height=48) if logo_image else None
    items = [img, Text(company_name, weight="bold", size=16)] if img else [
        Text(company_name, weight="bold", size=18)]
    row = Row(items, alignment="start", spacing=8)
    return Container(content=row, padding=8)


def make_side_nav(nav_items: List[Dict[str, Any]], collapsed: bool = False):
    lv = ListView(expand=True, spacing=6, padding=6, scroll=ScrollMode.AUTO)
    for it in nav_items:
        btn = ElevatedButton(it.get("label", ""), icon=it.get(
            "icon", None), on_click=it.get("on_click"))
        lv.controls.append(btn)
    width = NAV_WIDTH_COLLAPSED if collapsed else NAV_WIDTH_EXPANDED
    return Container(content=Column([lv], tight=True), width=width, bgcolor="#0f1720", padding=8)


def _try_go_back(page):
    try:
        if hasattr(page, "go_back"):
            page.go_back()
        elif hasattr(page, "navigate_back"):
            page.navigate_back()
    except Exception:
        pass


def inject_back_button(header_container, page):
    try:
        found = any(getattr(c, "tooltip", "") == "Back" for c in getattr(
            header_container, "controls", []))
        if not found:
            btn = IconButton("arrow_back", tooltip="Back",
                             on_click=lambda e: _try_go_back(page))
            header_container.controls.insert(0, btn)
            header_container.update()
    except Exception:
        pass


def make_app_shell(page, main_content, nav_items=None, logo_image=None, company_name="RadheFoundation", collapsed=False):
    if nav_items is None:
        nav_items = []
    header = Row([Text("")], alignment="spaceBetween")
    inject_back_button(header, page)
    left_panel = Column([make_logo_block(logo_image, company_name), make_side_nav(
        nav_items, collapsed)], tight=True)
    body = Row(
        [
            Container(content=left_panel, width=NAV_WIDTH_EXPANDED),
            Container(content=Column(
                [header, main_content], tight=False), expand=True, padding=12),
        ],
        expand=True,
        spacing=12,
        alignment="start",
    )
    return body


# ==================== UNIFIED UI COMPONENTS ====================

class LoadingButton:
    """
    A unified button component with loading state support.

    Usage:
        button = LoadingButton(
            text="Submit",
            on_click=handle_click,
            loading=False,
            bgcolor=PRIMARY_COLOR,
        )
    """

    @staticmethod
    def create(
        text: str,
        on_click: Optional[Callable] = None,
        loading: bool = False,
        bgcolor: str = PRIMARY_COLOR,
        color: str = Colors.WHITE,
        icon: Optional[str] = None,
        width: Optional[float] = None,
        height: float = 50,
        disabled: bool = False,
        expand: bool = False,
    ) -> Container:
        """
        Create a loading button.

        Args:
            text: Button text
            on_click: Click handler
            loading: Whether to show loading state
            bgcolor: Background color
            color: Text color
            icon: Optional icon
            width: Button width
            height: Button height
            disabled: Whether button is disabled
            expand: Whether to expand

        Returns:
            Container with the button
        """
        if loading:
            content = Row(
                [
                    ProgressRing(width=18, height=18,
                                 stroke_width=2, color=color),
                    Text(text, size=15, weight=FontWeight.W_500, color=color)
                ],
                alignment="center",
                spacing=8,
            )
        else:
            content = Row(
                [
                    Icon(icon, size=18, color=color) if icon else Container(),
                    Text(text, size=15, weight=FontWeight.W_500, color=color)
                ] if icon else [Text(text, size=15, weight=FontWeight.W_500, color=color)],
                alignment="center",
                spacing=8 if icon else 0,
            )

        return Container(
            content=content,
            width=width,
            height=height,
            bgcolor=bgcolor if not disabled else Colors.GREY_400,
            border_radius=BorderRadius(10, 10, 10, 10),
            alignment=alignment.Alignment(0, 0),
            on_click=None if disabled else on_click,
            ink=True,
            expand=expand,
        )


class LoadingOverlay:
    """
    A loading overlay component that covers the entire screen or a container.

    Usage:
        overlay = LoadingOverlay(
            message="Loading...",
            opacity=0.5,
        )
    """

    @staticmethod
    def create(
        message: str = "Loading...",
        opacity: float = 0.5,
        bgcolor: str = Colors.GREY_100,
    ) -> Container:
        """
        Create a loading overlay.

        Args:
            message: Loading message to display
            opacity: Overlay opacity
            bgcolor: Background color

        Returns:
            Container with the overlay
        """
        return Container(
            expand=True,
            bgcolor=Colors.with_opacity(opacity, bgcolor),
            content=Column(
                [
                    ProgressRing(width=40, height=40,
                                 stroke_width=3, color=PRIMARY_COLOR),
                    Container(height=10),
                    Text(message, size=14, color=Colors.GREY_700),
                ],
                alignment="center",
                horizontal_alignment="center",
            ),
            alignment=alignment.Alignment(0, 0),
        )


class UnifiedCard:
    """
    A unified card component with consistent styling.

    Usage:
        card = UnifiedCard(
            title="Card Title",
            content=column_controls,
            actions=[button1, button2],
        )
    """

    @staticmethod
    def create(
        title: Optional[str] = None,
        content: Optional[Any] = None,
        actions: Optional[List[Any]] = None,
        padding: int = 15,
        elevation: int = 1,
    ) -> Container:
        """
        Create a unified card.

        Args:
            title: Card title
            content: Card content (Control or list of controls)
            actions: Card action buttons
            padding: Padding inside card
            elevation: Card elevation

        Returns:
            Container with the card
        """
        card_content = []

        if title:
            card_content.append(
                Text(
                    title,
                    size=16,
                    weight=FontWeight.BOLD,
                    color="#1A1C1E",
                )
            )
            card_content.append(Container(height=10))

        if content:
            if isinstance(content, list):
                card_content.extend(content)
            else:
                card_content.append(content)

        if actions:
            card_content.append(Container(height=15))
            card_content.append(
                Row(actions, alignment="end", spacing=10)
            )

        return Container(
            padding=padding,
            border_radius=BorderRadius(10, 10, 10, 10),
            bgcolor=Colors.WHITE,
            border=Container(
                border=border.all(
                    1, Colors.with_opacity(0.1, Colors.GREY_400)),
            ),
            content=Column(card_content, tight=True),
        )


class StatusBadge:
    """
    A status badge component for displaying status labels.

    Usage:
        badge = StatusBadge(
            text="Active",
            color=SUCCESS_COLOR,
        )
    """

    @staticmethod
    def create(
        text: str,
        color: str = PRIMARY_COLOR,
        text_color: str = Colors.WHITE,
    ) -> Container:
        """
        Create a status badge.

        Args:
            text: Badge text
            color: Badge background color
            text_color: Text color

        Returns:
            Container with the badge
        """
        return Container(
            content=Text(
                text,
                size=11,
                weight=FontWeight.W_500,
                color=text_color,
            ),
            bgcolor=color,
            padding=padding.symmetric(horizontal=8, vertical=4),
            border_radius=BorderRadius(12, 12, 12, 12),
        )


class EmptyState:
    """
    An empty state component for displaying when there's no data.

    Usage:
        empty = EmptyState(
            icon=ft.Icons.INBOX_OUTLINED,
            title="No items",
            message="There are no items to display",
        )
    """

    @staticmethod
    def create(
        icon: str = ft.Icons.INBOX_OUTLINED,
        title: str = "No Data",
        message: str = "There's nothing to display here",
    ) -> Container:
        """
        Create an empty state.

        Args:
            icon: Icon to display
            title: Title text
            message: Description message

        Returns:
            Container with the empty state
        """
        return Container(
            content=Column(
                [
                    Icon(icon, size=64, color=Colors.GREY_400),
                    Container(height=15),
                    Text(
                        title,
                        size=18,
                        weight=FontWeight.W_500,
                        color=Colors.GREY_700,
                        text_align=TextAlign.CENTER,
                    ),
                    Container(height=5),
                    Text(
                        message,
                        size=14,
                        color=Colors.GREY_500,
                        text_align=TextAlign.CENTER,
                    ),
                ],
                alignment="center",
                horizontal_alignment="center",
            ),
            padding=30,
        )


class ConfirmDialog:
    """
    A confirmation dialog component.

    Usage:
        dialog = ConfirmDialog(
            title="Confirm",
            message="Are you sure?",
            confirm_text="Yes",
            cancel_text="No",
            on_confirm=handle_confirm,
            on_cancel=handle_cancel,
        )
    """

    @staticmethod
    def create(
        page,
        title: str,
        message: str,
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
        confirm_color: str = DANGER_COLOR,
        on_confirm: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None,
    ) -> AlertDialog:
        """
        Create a confirmation dialog.

        Args:
            page: Flet page
            title: Dialog title
            message: Dialog message
            confirm_text: Confirm button text
            cancel_text: Cancel button text
            confirm_color: Confirm button color
            on_confirm: Confirm handler
            on_cancel: Cancel handler

        Returns:
            AlertDialog
        """
        def handle_confirm(e):
            if on_confirm:
                on_confirm(e)
            page.dialog = None
            page.update()

        def handle_cancel(e):
            if on_cancel:
                on_cancel(e)
            page.dialog = None
            page.update()

        return AlertDialog(
            title=Text(title),
            content=Text(message),
            actions=[
                TextButton(cancel_text, on_click=handle_cancel),
                ElevatedButton(
                    confirm_text,
                    on_click=handle_confirm,
                    style=ButtonStyle(bgcolor=confirm_color,
                                      color=Colors.WHITE),
                ),
            ],
            actions_alignment="end",
        )


# ==================== UTILITY FUNCTIONS ====================

def show_snackbar(page, message: str, bgcolor: str = "#323232", duration: int = 3):
    """
    Show a snackbar message.

    Args:
        page: Flet page
        message: Message to display
        bgcolor: Background color
        duration: Duration in seconds
    """
    try:
        snack = SnackBar(
            content=Text(message),
            bgcolor=bgcolor,
            duration=duration,
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()
    except Exception as e:
        print(f"Snackbar error: {e}")


def show_loading_dialog(page, message: str = "Loading..."):
    """
    Show a loading dialog.

    Args:
        page: Flet page
        message: Loading message

    Returns:
        AlertDialog (open)
    """
    dialog = AlertDialog(
        content=Column(
            [
                ProgressRing(),
                Container(height=10),
                Text(message),
            ],
            alignment="center",
            horizontal_alignment="center",
        ),
        open=True,
    )
    page.dialog = dialog
    page.update()
    return dialog


def hide_loading_dialog(page):
    """
    Hide the loading dialog.

    Args:
        page: Flet page
    """
    page.dialog = None
    page.update()


# Import additional flet components needed
