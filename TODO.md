# Vernika Deployment Fixes - TODO

## Issue 1: Missing `requests` module (CRITICAL) ✅ DONE
- [x] Add requests to requirements-web.txt

## Issue 2: Logo & Profile Photos Not Visible ✅ DONE
- [x] Created web_helpers.py for proper URL handling
- [x] Updated logo paths in login_screen.py to use /assets/logo/Vernikalogo.png
- [x] Updated logo paths in employee_screen.py to use /assets/logo/Vernikalogo.png
- [x] Updated logo paths in dashboard_screen.py to use /assets/logo/Vernikalogo.png

## Issue 3: Responsive Design for All Screen Sizes ✅ DONE
- [x] Created responsive layout helpers in utils/web_helpers.py
- [x] Fixed login_screen.py for mobile (combines panels vertically)
- [x] Fixed employee_screen.py sidebar responsiveness (hidden on mobile, icon-only on tablet)
- [x] Fixed dashboard_screen.py (sidebar hidden on mobile)
- [x] Fixed admin_screen.py responsiveness (hidden on mobile, icon-only on tablet)
- [x] Updated web_main.py for responsive window (min_width=320, min_height=568)

## Issue 4: Supabase Storage URL Handling ✅ DONE
- [x] Updated supabase_storage.py to handle web URLs properly
- [x] Added better error handling for missing requests module

## Summary of Changes Made:
1. **requirements-web.txt**: Added `requests>=2.31.0`
2. **utils/web_helpers.py**: New file with responsive helpers
3. **screens/login_screen.py**: Responsive design with mobile vertical layout
4. **screens/employee_screen.py**: Responsive sidebar (hidden on mobile)
5. **screens/dashboard_screen.py**: Fixed logo path
6. **screens/admin_screen.py**: Responsive sidebar (hidden on mobile)
7. **web_main.py**: Updated window settings for mobile support
8. **utils/supabase_storage.py**: Better error handling

## To Deploy:
1. Push changes to GitHub
2. Render will automatically redeploy
3. Test on different screen sizes

