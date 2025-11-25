# Admin Panel Documentation

## Overview
The admin panel allows you to dynamically manage the login page without editing code. You can control features, appearance, and social login buttons in real-time.

## Accessing the Admin Panel

1. **Login to Dashboard**: Navigate to `/dashboard` and login with your password
2. **Access Admin Panel**: Click the "⚙️ Admin Panel" button or go to `/admin`

## Features

### 🔐 Login Features
- **Google Login Button**: Toggle on/off the Google OAuth login button
- **Facebook Login Button**: Toggle on/off the Facebook login button (requires Facebook OAuth setup)

### 🎨 Page Appearance
- **Page Title**: Customize the main heading on the login page
- **Button Text**: Change the text on the main login button
- **Background Image**: Set a custom background image URL (CSS format: `url(path/to/image.jpg)`)
- **Background Color**: Set a fallback background color (used when no image or as gradient overlay)

## How It Works

### Database Structure
Settings are stored in the `page_settings` table with the following schema:
```sql
CREATE TABLE page_settings (
    id SERIAL PRIMARY KEY,
    setting_key TEXT UNIQUE NOT NULL,
    setting_value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Default Settings
```python
google_login_enabled: 'true'
facebook_login_enabled: 'false'
background_image: 'url(../img/nuanu.png)'
background_color: '#667eea'
page_title: 'Welcome To NUANU Free WiFi'
button_text: 'Connect to WiFi'
```

## API Endpoints

### Get Settings
```
GET /api/settings
```
Returns all current page settings as JSON.

### Update Settings
```
POST /api/settings
Authorization: Required (session-based)
Content-Type: application/json

{
  "google_login_enabled": "true",
  "facebook_login_enabled": "false",
  "background_image": "url(../img/nuanu.png)",
  "background_color": "#667eea",
  "page_title": "Welcome To NUANU Free WiFi",
  "button_text": "Connect to WiFi"
}
```

## Pages

### `/login` - Dynamic Login Page
The main login page that reads settings from the database and renders accordingly. Changes made in the admin panel are reflected immediately on this page.

### `/admin` - Admin Panel
Protected page (requires dashboard login) where you can manage all settings.

### `/dashboard` - Email Dashboard
View collected emails with a link to the admin panel.

## Usage Examples

### Example 1: Disable Social Login
1. Go to `/admin`
2. Toggle off "Google Login Button"
3. Click "💾 Save Settings"
4. Visit `/login` - Google button is now hidden

### Example 2: Change Background
1. Go to `/admin`
2. Update "Background Image URL" to `url(https://example.com/new-bg.jpg)`
3. Update "Background Color" to `#ff6b6b`
4. Click "💾 Save Settings"
5. Visit `/login` - New background is applied

### Example 3: Customize Text
1. Go to `/admin`
2. Change "Page Title" to "Free WiFi Access"
3. Change "Button Text" to "Get Connected"
4. Click "💾 Save Settings"
5. Visit `/login` - New text is displayed

## Technical Details

### Functions Added to `app.py`

1. **`init_db()`**: Creates `page_settings` table and inserts default values
2. **`get_page_settings()`**: Retrieves all settings as a dictionary
3. **`update_page_setting(key, value)`**: Updates a specific setting

### Routes Added

1. **`GET /admin`**: Admin panel UI
2. **`POST /api/settings`**: Update settings endpoint
3. **`GET /api/settings`**: Get settings endpoint
4. **`GET /login`**: Dynamic login page (replaces static `login.html`)

## Security

- Admin panel requires authentication via `/dashboard` login
- Settings API endpoints are protected with session-based authentication
- Only authenticated users can modify settings

## Deployment

After making changes to `app.py`, restart your application:

```bash
# On Digital Ocean or Railway
# The app will auto-restart on git push

# Or manually restart
pkill -f "uvicorn app:app"
uvicorn app:app --host 0.0.0.0 --port 8000
```

## Troubleshooting

### Settings not saving
- Check if you're logged in to the dashboard
- Check browser console for errors
- Verify database connection

### Login page not updating
- Hard refresh the page (Ctrl+F5)
- Clear browser cache
- Check if settings were saved successfully

### Social login buttons not working
- Ensure OAuth credentials are configured in environment variables
- Check `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
- For Facebook, implement OAuth configuration similar to Google

## Future Enhancements

Potential features to add:
- Upload custom background images
- Multiple theme presets
- Custom CSS editor
- Logo upload
- Email template customization
- Multi-language support
