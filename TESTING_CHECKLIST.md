# 🧪 Testing Checklist - Admin Panel

## ✅ Server is Running!
Your local test server is now running at: **http://127.0.0.1:8000**

## Step-by-Step Testing Guide

### 1️⃣ Test Dashboard Login
- [ ] Open: http://127.0.0.1:8000/dashboard
- [ ] Enter password: `Bali0361`
- [ ] Click "Login"
- [ ] ✅ Should see email dashboard with sample data

### 2️⃣ Access Admin Panel
- [ ] Click "⚙️ Admin Panel" button on dashboard
- [ ] OR go to: http://127.0.0.1:8000/admin
- [ ] ✅ Should see admin panel with settings

### 3️⃣ Test Feature Toggles
- [ ] Toggle "Google Login Button" OFF
- [ ] Click "💾 Save Settings"
- [ ] ✅ Should see success message
- [ ] Open http://127.0.0.1:8000/login in new tab
- [ ] ✅ Google button should be HIDDEN

- [ ] Go back to admin panel
- [ ] Toggle "Google Login Button" ON
- [ ] Click "💾 Save Settings"
- [ ] Refresh login page
- [ ] ✅ Google button should be VISIBLE

### 4️⃣ Test Text Changes
- [ ] In admin panel, change "Page Title" to: `Test WiFi Access`
- [ ] Change "Button Text" to: `Get Connected Now`
- [ ] Click "💾 Save Settings"
- [ ] Refresh login page
- [ ] ✅ Should see new title and button text

### 5️⃣ Test Background Color
- [ ] In admin panel, click the color picker
- [ ] Choose a different color (e.g., red #ff0000)
- [ ] Click "💾 Save Settings"
- [ ] Refresh login page
- [ ] ✅ Background should change to new color

### 6️⃣ Test Background Image
- [ ] In admin panel, change "Background Image URL" to:
  ```
  url(https://images.unsplash.com/photo-1557683316-973673baf926?w=1920)
  ```
- [ ] Click "💾 Save Settings"
- [ ] Refresh login page
- [ ] ✅ Should see new background image

### 7️⃣ Test Preview Link
- [ ] In admin panel, click "Preview Login Page →"
- [ ] ✅ Should open login page in new tab with your changes

### 8️⃣ Test Logout
- [ ] Click "Back to Dashboard"
- [ ] Click "Logout"
- [ ] ✅ Should return to login screen

## Quick Access URLs

| Page | URL |
|------|-----|
| **Dashboard** | http://127.0.0.1:8000/dashboard |
| **Admin Panel** | http://127.0.0.1:8000/admin |
| **Login Page** | http://127.0.0.1:8000/login |
| **API Settings** | http://127.0.0.1:8000/api/settings |

## Default Credentials
- **Password**: `Bali0361`

## What to Look For

### ✅ Success Indicators
- Green success message after saving
- Changes appear immediately on login page
- Smooth toggle switches
- Color picker works
- All buttons clickable

### ❌ Potential Issues
- If changes don't appear: Hard refresh (Ctrl + F5)
- If can't login: Check password is exactly `Bali0361`
- If server crashes: Check terminal for errors

## Testing Tips

1. **Keep two tabs open**: Admin panel + Login page
2. **Use Ctrl + F5** to hard refresh and see changes
3. **Test one feature at a time** to isolate issues
4. **Check browser console** (F12) for JavaScript errors

## After Testing

When you're done testing:
1. Press `Ctrl + C` in the terminal to stop the server
2. Or close the terminal window

## Notes

- This is using your **production database**
- Changes you make **WILL affect production** if database is connected
- The database connection is to Digital Ocean PostgreSQL
- All settings are stored in the `page_settings` table

## Next Steps

Once testing is complete and you're happy with the features:
1. Commit changes: `git add .`
2. Commit: `git commit -m "Add dynamic admin panel"`
3. Push to production: `git push origin main`
4. Your Digital Ocean app will auto-deploy!

---

**🎉 Happy Testing!**
