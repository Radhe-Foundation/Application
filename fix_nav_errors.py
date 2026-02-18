#!/usr/bin/env python3
"""Fix navigate_to_home import errors in all screen files"""
import os
import re

screens_dir = 'screens'
fixed_files = []

for filename in os.listdir(screens_dir):
    if filename.endswith('.py') and filename != '__init__.py':
        filepath = os.path.join(screens_dir, filename)
        with open(filepath, 'r') as f:
            content = f.read()

        # Check for the problematic import
        if 'from core.navigation import navigate_to_home' in content:
            # Replace the import
            content = content.replace(
                'from core.navigation import navigate_to_home',
                '# Navigation import removed'
            )

            # Fix the on_back function pattern
            patterns = [
                (r'def on_back\(self, e\):.*?navigate_to_home\(self\._page, self\.user\)',
                 '''def on_back(self, e):
        """Go back to admin screen"""
        from screens.admin_screen import AdminScreen
        self._page.clean()
        self._page.add(AdminScreen(self._page, self.user))'''),
                (r'def on_back\(self, e\):.*?navigate_to_home\(self\._page\)',
                 '''def on_back(self, e):
        """Go back to admin screen"""
        from screens.admin_screen import AdminScreen
        self._page.clean()
        self._page.add(AdminScreen(self._page, self.user))'''),
            ]

            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement,
                                 content, flags=re.DOTALL)

            with open(filepath, 'w') as f:
                f.write(content)
            fixed_files.append(filename)
            print(f"Fixed: {filename}")

print(f"\nTotal files fixed: {len(fixed_files)}")
