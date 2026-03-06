# Vernika HRA - Deployment Guide

## Overview
Your Vernika HRA application is built with **Flet**, which natively supports both **Web** and **Mobile (APK)** deployment. This guide covers both options.

---

## Option 1: Web Deployment (Access from any OS)

### Prerequisites
```bash
pip install flet[web]>=0.25.0
```

### Method 1: Build and Host on Vercel (Recommended)

#### Step 1: Create web entry point
Create a new file `web_main.py`:

```python
import flet as ft
from main import init_db, check_database_health

def main(page: ft.Page):
    # Your existing main logic from main.py
    from core.navigation_v2 import init_navigation
    from core.keyboard_shortcuts_v2 import init_keyboard_shortcuts
    from utils.notification_manager import init_notification_manager
    from screens.login_screen import LoginScreen
    
    page.title = "Vernika HRA"
    page.window.min_width = 1024
    page.window.min_height = 768
    
    # Initialize components (same as desktop)
    if check_database_health():
        init_db()
        init_navigation(page)
        init_keyboard_shortcuts(page)
        init_notification_manager(page)
        login_screen = LoginScreen(page)
        page.add(login_screen)

ft.app(target=main, web=True)
```

#### Step 2: Create `vercel.json`
```json
{
  "builds": [
    {
      "src": "web_main.py",
      "use": "@fletco/vercel-adapter"
    }
  ],
  "routes": [
    {
      "src": "/(.*)"
    }
  ]
}
```

#### Step 3: Deploy to Vercel
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

#### Alternative: Build HTML and host anywhere
```bash
flet build web --publish --domain "your-domain.com"
# Output in ./build/web folder
```

---

### Method 2: Build and Host on Railway/Render

#### Step 1: Create `requirements-web.txt`
```
flet[web]>=0.25.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
python-dotenv>=1.0.0
bcrypt>=4.0.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
pillow>=10.0.0
python-dateutil>=2.8.2
pydantic>=2.0.0
email-validator>=2.0.0
```

#### Step 2: Create `Procfile`
```
web: python -m flet web_main
```

**Note for Render:** If you created the service manually in Render dashboard, the YAML config may be cached. Go to your service settings in Render and ensure the "Start Command" is set to:
```
python -m flet web_main
```

#### Step 3: Deploy to Railway
1. Push code to GitHub
2. Connect Railway to GitHub repo
3. Add environment variables (DATABASE_URL, SUPABASE_URL, etc.)
4. Deploy!

---

### Method 3: Build HTML and Use CDN

```bash
flet build web
# Outputs to ./build/web folder

# Upload the build/web folder to any static hosting:
# - Netlify
# - GitHub Pages
# - Cloudflare Pages
# - AWS S3 + CloudFront
```

---

## Option 2: APK Deployment (Android Mobile App)

### Prerequisites
```bash
# Install Flet with mobile support
pip install flet[mobile]>=0.25.0

# For building APK, you need:
# - Android SDK (install Android Studio)
# - Java JDK 11+
```

### Build APK

```bash
# Basic APK build
flet build apk --publish --android-app-name "VernikaHRA"

# With custom icon
flet build apk --publish --icon ./assets/logo/Vernikalogo.png

# With bundle (for Play Store)
flet build bundle --android
```

### Output
- **APK**: `./build/apk/app-release.apk`
- **AAB (for Play Store)**: `./build/app-release.aab`

---

## Option 3: iOS App (Optional)

```bash
# For macOS only - requires Xcode
flet build ios --publish
```

---

## Summary: Best Approach for Your Use Case

| Option | Use Case | Difficulty |
|--------|----------|------------|
| **Vercel (Web)** | Access from any browser, any OS | ⭐ Easy |
| **Railway/Render (Web)** | Full web app with backend | ⭐⭐ Medium |
| **APK (Android)** | Mobile app for employees | ⭐ Easy |
| **iOS** | Mobile app for iPhone users | ⭐⭐⭐ Hard (Mac required) |

---

## Recommended Deployment Path

1. **Start with Web on Vercel** - Easiest, available
2. **Build APK** free tier for mobile users
3. **Consider PWA** - Add to home screen, works like native app

---

## Environment Variables for Production

When deploying, ensure these are set:

```
# Database
DATABASE_URL=postgresql://...

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Security
SECRET_KEY=your-production-secret-key

# App Settings
ENVIRONMENT=production
THEME_MODE=light
```

---

## Troubleshooting

### Web Issues
- **Database connection**: Ensure DATABASE_URL is accessible (use Supabase for cloud DB)
- **CORS errors**: Update CORS_ORIGINS in config.py for your domain
- **Session issues**: Use production-ready session management

### APK Issues
- **Build fails**: Check Android SDK path
- **App crashes**: Check logs with `adb logcat`
- **Storage permission**: Add to manifest if needed

---

## Cost Estimates

| Platform | Free Tier | Paid |
|----------|-----------|------|
| Vercel | 100GB bandwidth/month | $20+/mo |
| Railway | $5 credit/month | $20+/mo |
| Render | 750 hours/month | $7+/mo |
| Supabase | 500MB DB, 1GB storage | $25+/mo |
