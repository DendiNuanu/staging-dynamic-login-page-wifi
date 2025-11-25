# Local Testing Guide

## Quick Start - 3 Steps

### Step 1: Install Dependencies
```powershell
cd d:\SERVER-DO\welcome-to-nuanu-login-page-wifi
pip install fastapi uvicorn starlette authlib httpx python-multipart
```

### Step 2: Run Test Server
```powershell
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

### Step 3: Open Browser
- Dashboard: http://127.0.0.1:8000/dashboard
- Password: `Bali0361`
- Admin Panel: http://127.0.0.1:8000/admin
- Login Page: http://127.0.0.1:8000/login

## What to Test

### ✅ Test Admin Panel
1. Go to http://127.0.0.1:8000/dashboard
2. Login with password: `Bali0361`
3. Click "⚙️ Admin Panel"
4. Try these changes:
   - Toggle Google Login on/off
   - Change page title to "Test WiFi"
   - Change button text to "Get Online"
   - Change background color
   - Click "💾 Save Settings"

### ✅ Test Login Page
1. Open http://127.0.0.1:8000/login in new tab
2. See your changes applied!
3. Refresh to see updates

## Troubleshooting

### Error: Database connection failed
**Solution**: The app will try to connect to production database. This is OK for testing the UI, but email saving won't work locally.

### Error: Port already in use
**Solution**: Use a different port:
```powershell
uvicorn app:app --reload --host 127.0.0.1 --port 8001
```
Then visit: http://127.0.0.1:8001/dashboard

### Changes not showing
**Solution**: Hard refresh the page (Ctrl + F5)

## Notes

- Local testing uses your production database (read-only for settings)
- Changes you make in admin panel WILL affect production if database is connected
- To test safely without affecting production, disconnect from database first
