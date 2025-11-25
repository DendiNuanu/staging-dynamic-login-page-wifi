# Quick Start Guide - Admin Panel

## ✅ YES! You can now manage your login page dynamically!

## What's New?

Your WiFi login page is now **fully dynamic** with an admin panel that lets you:

✅ **Toggle Google Login** - Turn on/off the Google OAuth button  
✅ **Toggle Facebook Login** - Turn on/off the Facebook OAuth button  
✅ **Change Background** - Upload new background images or use solid colors  
✅ **Customize Text** - Change page title and button text  
✅ **Real-time Updates** - Changes apply immediately without code edits  

## How to Use

### Step 1: Access the Admin Panel
1. Go to your website: `https://your-domain.com/dashboard`
2. Login with password: `Bali0361` (or your configured password)
3. Click the **"⚙️ Admin Panel"** button

### Step 2: Make Changes
- **Toggle Features**: Use the switches to enable/disable login buttons
- **Change Appearance**: Update colors, images, and text
- **Save**: Click **"💾 Save Settings"** button

### Step 3: Preview
- Click **"Preview Login Page →"** to see your changes
- Or visit: `https://your-domain.com/login`

## Example Changes

### Disable Google Login
1. Go to Admin Panel
2. Toggle off "Google Login Button"
3. Save
4. ✅ Google button is now hidden on login page

### Change Background Color
1. Go to Admin Panel
2. Click the color picker under "Background Color"
3. Select your color (e.g., red, blue, green)
4. Save
5. ✅ New color appears on login page

### Change Page Title
1. Go to Admin Panel
2. Update "Page Title" field (e.g., "Welcome to Free WiFi")
3. Save
4. ✅ New title shows on login page

## Important URLs

- **Login Page**: `/login` (your users see this)
- **Dashboard**: `/dashboard` (view collected emails)
- **Admin Panel**: `/admin` (manage page settings)

## Database

All settings are stored in PostgreSQL table `page_settings`:
- Settings persist across server restarts
- Changes are instant
- No code deployment needed

## Deployment

Your changes are already in `app.py`. To deploy:

```bash
# Commit changes
git add .
git commit -m "Add dynamic admin panel"
git push origin main

# Your Digital Ocean app will auto-deploy
```

## Need Help?

Check `ADMIN_PANEL_README.md` for detailed documentation.

## What's Changed in the Code?

### Files Modified:
- ✅ `app.py` - Added admin panel, API endpoints, and dynamic login page

### New Features:
- ✅ Database table `page_settings`
- ✅ Admin panel UI at `/admin`
- ✅ Settings API at `/api/settings`
- ✅ Dynamic login page at `/login`
- ✅ Helper functions for settings management

### No Breaking Changes:
- ✅ All existing features still work
- ✅ Email collection still works
- ✅ Dashboard still works
- ✅ Google OAuth still works

---

**🎉 Congratulations! Your login page is now fully dynamic and manageable!**
