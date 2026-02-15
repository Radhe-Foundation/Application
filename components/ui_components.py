from typing import List, Dict, Any
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
    icons,
)

NAV_WIDTH_EXPANDED = 260
NAV_WIDTH_COLLAPSED = 64

def make_logo_block(logo_image: str | None = None, company_name: str = "Vernika"):
    img = Image(src=logo_image, height=48) if logo_image else None
    items = [img, Text(company_name, weight="bold", size=16)] if img else [Text(company_name, weight="bold", size=18)]
    row = Row(items, alignment="start", spacing=8)
    return Container(content=row, padding=8)

def make_side_nav(nav_items: List[Dict[str, Any]], collapsed: bool = False):
    lv = ListView(expand=True, spacing=6, padding=6, scroll=ScrollMode.AUTO)
    for it in nav_items:
        btn = ElevatedButton(it.get("label", ""), icon=it.get("icon", None), on_click=it.get("on_click"))
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
        found = any(getattr(c, "tooltip", "") == "Back" for c in getattr(header_container, "controls", []))
        if not found:
            btn = IconButton("arrow_back", tooltip="Back", on_click=lambda e: _try_go_back(page))
            header_container.controls.insert(0, btn)
            header_container.update()
    except Exception:
        pass

def make_app_shell(page, main_content, nav_items=None, logo_image=None, company_name="Vernika", collapsed=False):
    if nav_items is None:
        nav_items = []
    header = Row([Text("")], alignment="spaceBetween")
    inject_back_button(header, page)
    left_panel = Column([make_logo_block(logo_image, company_name), make_side_nav(nav_items, collapsed)], tight=True)
    body = Row(
        [
            Container(content=left_panel, width=NAV_WIDTH_EXPANDED),
            Container(content=Column([header, main_content], tight=False), expand=True, padding=12),
        ],
        expand=True,
        spacing=12,
        alignment="start",
    )
    return body
