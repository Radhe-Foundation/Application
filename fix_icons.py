#!/usr/bin/env python3
"""
Fix icon references in chat_screen.py
Change icons.XXX to ft.Icons.XXX
"""

# Read the file
with open('/Users/shashankrajput/Desktop/Vernika/screens/chat_screen.py', 'r') as f:
    content = f.read()

# Count before
before_count = content.count('icons.')

# Replace icons. with ft.Icons.
content = content.replace('icons.CHAT', 'ft.Icons.CHAT')
content = content.replace('icons.EVENT', 'ft.Icons.EVENT')
content = content.replace('icons.EMAIL', 'ft.Icons.EMAIL')
content = content.replace('icons.FOLDER', 'ft.Icons.FOLDER')
content = content.replace('icons.PEOPLE', 'ft.Icons.PEOPLE')
content = content.replace('icons.GROUPS', 'ft.Icons.GROUPS')
content = content.replace('icons.ADD', 'ft.Icons.ADD')
content = content.replace('icons.ARROW_BACK', 'ft.Icons.ARROW_BACK')
content = content.replace('icons.PERSON', 'ft.Icons.PERSON')
content = content.replace('icons.VIDEO_CALL', 'ft.Icons.VIDEO_CALL')
content = content.replace('icons.PHONE', 'ft.Icons.PHONE')
content = content.replace('icons.ATTACH_FILE', 'ft.Icons.ATTACH_FILE')
content = content.replace('icons.EMOJI_EMOTIONS', 'ft.Icons.EMOJI_EMOTIONS')
content = content.replace('icons.SEND', 'ft.Icons.SEND')
content = content.replace('icons.SCHEDULE', 'ft.Icons.SCHEDULE')
content = content.replace('icons.CREATE', 'ft.Icons.CREATE')
content = content.replace('icons.DOWNLOAD', 'ft.Icons.DOWNLOAD')
content = content.replace('icons.UPLOAD_FILE', 'ft.Icons.UPLOAD_FILE')
content = content.replace('icons.GROUPS_ADD', 'ft.Icons.GROUPS_ADD')

# Count after
after_count = content.count('ft.Icons.')

print(f"Replaced {before_count} 'icons.' references with 'ft.Icons.'")

# Write the file
with open('/Users/shashankrajput/Desktop/Vernika/screens/chat_screen.py', 'w') as f:
    f.write(content)

print("File updated successfully!")
