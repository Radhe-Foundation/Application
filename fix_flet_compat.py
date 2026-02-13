#!/usr/bin/env python3
"""
Vernika Flet Compatibility Fix Script
Fixes deprecated Flet patterns for version 0.80.5+
"""

import os
import re


def fix_file(filepath):
    """Fix deprecated Flet patterns in a file"""
    with open(filepath, 'r') as f:
        content = f.read()

    original = content

    # Fix 1: weight="bold" -> weight=ft.FontWeight.BOLD
    content = re.sub(r'weight="bold"', 'weight=ft.FontWeight.BOLD', content)
    content = re.sub(r'weight="normal"',
                     'weight=ft.FontWeight.NORMAL', content)

    # Fix 2: scroll="auto" -> scroll=ft.ScrollMode.AUTO
    content = re.sub(r'scroll="auto"', 'scroll=ft.ScrollMode.AUTO', content)
    content = re.sub(r'scroll=True', 'scroll=ft.ScrollMode.AUTO', content)

    # Fix 3: alignment="center" -> alignment=ft.MainAxisAlignment.CENTER
    content = re.sub(r'alignment="center"',
                     'alignment=ft.MainAxisAlignment.CENTER', content)
    content = re.sub(r'alignment="spaceBetween"',
                     'alignment=ft.MainAxisAlignment.SPACE_BETWEEN', content)
    content = re.sub(r'alignment="spaceAround"',
                     'alignment=ft.MainAxisAlignment.SPACE_AROUND', content)
    content = re.sub(r'alignment="end"',
                     'alignment=ft.MainAxisAlignment.END', content)
    content = re.sub(r'alignment="start"',
                     'alignment=ft.MainAxisAlignment.START', content)

    # Fix 4: horizontal_alignment="center" -> horizontal_alignment=ft.CrossAxisAlignment.CENTER
    content = re.sub(r'horizontal_alignment="center"',
                     'horizontal_alignment=ft.CrossAxisAlignment.CENTER', content)
    content = re.sub(r'horizontal_alignment="start"',
                     'horizontal_alignment=ft.CrossAxisAlignment.START', content)
    content = re.sub(r'horizontal_alignment="end"',
                     'horizontal_alignment=ft.CrossAxisAlignment.END', content)

    # Fix 5: vertical_alignment="center" -> vertical_alignment=ft.CrossAxisAlignment.CENTER
    content = re.sub(r'vertical_alignment="center"',
                     'vertical_alignment=ft.CrossAxisAlignment.CENTER', content)

    # Fix 6: padding.all(10) -> padding=padding.all(10)
    content = re.sub(r'padding\.all\((\d+)\)',
                     r'padding=padding.all(\1)', content)
    content = re.sub(r'padding\.symmetric\(',
                     'padding=padding.symmetric(', content)

    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed: {filepath}")
        return True
    return False


def main():
    """Fix all screen files"""
    screens_dir = "/Users/shashankrajput/Desktop/Vernika/screens"

    files_to_fix = [
        f"{screens_dir}/admin_screen.py",
        f"{screens_dir}/dashboard_screen.py",
        f"{screens_dir}/chat_screen.py",
        f"{screens_dir}/profile_screen.py",
        f"{screens_dir}/attendance_screen.py",
        f"{screens_dir}/leaves_screen.py",
        f"{screens_dir}/tasks_screen.py",
        f"{screens_dir}/employees_screen.py",
        f"{screens_dir}/departments_screen.py",
        f"{screens_dir}/positions_screen.py",
        f"{screens_dir}/base_screen.py",
    ]

    for filepath in files_to_fix:
        if os.path.exists(filepath):
            fix_file(filepath)

    print("\nAll files fixed!")


if __name__ == "__main__":
    main()
