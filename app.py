from fastapi import FastAPI, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request as StarletteRequest
from authlib.integrations.starlette_client import OAuth
try:
    from dotenv import load_dotenv  # type: ignore
    _HAS_DOTENV = True
except Exception:
    _HAS_DOTENV = False
    def load_dotenv(*args, **kwargs):
        return False
import psycopg2
import os
import html
import csv
from io import StringIO, BytesIO
from datetime import datetime, timedelta, date, time
from typing import Optional, Tuple, List




# Optional imports for export formats
try:
    from openpyxl import Workbook
except Exception:
    Workbook = None  # type: ignore

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
except Exception:
    SimpleDocTemplate = None  # type: ignore

def _ensure_env_file():
    """Create a basic .env on first run so the app can boot with sane defaults."""
    try:
        if not os.path.exists(".env"):
            with open(".env", "w", encoding="utf-8") as f:
                f.write(
                    "BASE_URL=http://127.0.0.1:8000\n"
                    "GOOGLE_CLIENT_ID=\n"
                    "GOOGLE_CLIENT_SECRET=\n"
                    "FACEBOOK_CLIENT_ID=\n"
                    "FACEBOOK_CLIENT_SECRET=\n"
                    "DASHBOARD_PASSWORD=Nuanu0361\n"
                    "GATEWAY_IP=172.19.20.1\n"
                    "HOTSPOT_USER=user\n"
                    "HOTSPOT_PASS=user\n"
                    "DST_URL=https://nuanu.com/\n"
                    "SECRET_KEY=super-secret-key\n"
                )
    except Exception:
        # Fail silently; the app still has hard-coded fallbacks
        pass

_ensure_env_file()
if _HAS_DOTENV:
    load_dotenv()  # Load variables from .env if present (created above on first run)

app = FastAPI()

# ==== Static Files ====
app.mount("/img", StaticFiles(directory="img"), name="img")

# ==== Session Middleware ====
# Configure session with proper cookie settings for OAuth
app.add_middleware(
    SessionMiddleware, 
    secret_key=os.getenv("SECRET_KEY", "super-secret-key"),
    max_age=3600,  # 1 hour
    same_site="lax",  # Allow cookies to be sent on cross-site redirects
    https_only=False  # Allow cookies on http for local development
)

# ==== CORS ====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()
# ==== Konfigurasi Database ====
# ==== Konfigurasi Database ====
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "sslmode": "require"
}

def get_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")
        # Try to reconnect with more detailed error handling
        try:
            # Try with a timeout
            conn = psycopg2.connect(
                dbname=DB_CONFIG['dbname'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                sslmode=DB_CONFIG['sslmode'],
                connect_timeout=5
            )
            return conn
        except Exception as e:
            print(f"Failed to connect to database: {str(e)}")
            # Create a simple in-memory database for fallback
            import sqlite3
            print("Falling back to SQLite in-memory database")
            return sqlite3.connect(":memory:")

DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "Nuanu0361")

# ==== URL Aplikasi ====
BASE_URL = os.getenv("BASE_URL", "https://wifi.nuanu.io")

# ==== Mikrotik Hotspot ====
GATEWAY_IP = os.getenv("GATEWAY_IP", "172.19.20.1")
HOTSPOT_USER = os.getenv("HOTSPOT_USER", "user")
HOTSPOT_PASS = os.getenv("HOTSPOT_PASS", "user")
DST_URL = os.getenv("DST_URL", "https://nuanu.com/")

# ==== Google OAuth ====
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
FACEBOOK_CLIENT_ID = os.getenv("FACEBOOK_CLIENT_ID")
FACEBOOK_CLIENT_SECRET = os.getenv("FACEBOOK_CLIENT_SECRET")

oauth = OAuth()

def reload_oauth_config():
    """Reload OAuth configuration from environment variables"""
    global GOOGLE_OAUTH_ENABLED, FACEBOOK_OAUTH_ENABLED, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, FACEBOOK_CLIENT_ID, FACEBOOK_CLIENT_SECRET
    
    # Reload environment variables
    if _HAS_DOTENV:
        load_dotenv(override=True)
    
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID") or ""
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET") or ""
    FACEBOOK_CLIENT_ID = os.getenv("FACEBOOK_CLIENT_ID") or ""
    FACEBOOK_CLIENT_SECRET = os.getenv("FACEBOOK_CLIENT_SECRET") or ""
    
    # Unregister existing if any - try multiple methods
    try:
        if hasattr(oauth, '_clients') and isinstance(oauth._clients, dict):
            oauth._clients.pop("google", None)
            oauth._clients.pop("facebook", None)
    except Exception:
        pass
    
    # Create a new OAuth instance to clear old registrations
    # We'll re-register below
    try:
        # Try to unregister by re-registering with empty values first
        pass
    except Exception:
        pass
    
    # Register Google OAuth (only if both ID and secret are provided)
    GOOGLE_OAUTH_ENABLED = bool(GOOGLE_CLIENT_ID.strip() and GOOGLE_CLIENT_SECRET.strip())
    if GOOGLE_OAUTH_ENABLED:
        try:
            # Unregister first if exists
            if "google" in oauth._clients:
                del oauth._clients["google"]
            oauth.register(
                name="google",
                client_id=GOOGLE_CLIENT_ID,
                client_secret=GOOGLE_CLIENT_SECRET,
                server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
                client_kwargs={"scope": "openid email profile"},
            )
        except (KeyError, AttributeError):
            # If _clients doesn't exist or key doesn't exist, just register
            try:
                oauth.register(
                    name="google",
                    client_id=GOOGLE_CLIENT_ID,
                    client_secret=GOOGLE_CLIENT_SECRET,
                    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
                    client_kwargs={"scope": "openid email profile"},
                )
            except Exception as e:
                print(f"Error registering Google OAuth: {e}")
                GOOGLE_OAUTH_ENABLED = False
        except Exception as e:
            print(f"Error registering Google OAuth: {e}")
            GOOGLE_OAUTH_ENABLED = False
    else:
        GOOGLE_OAUTH_ENABLED = False
    
    # Register Facebook OAuth (only if both ID and secret are provided)
    FACEBOOK_OAUTH_ENABLED = bool(FACEBOOK_CLIENT_ID.strip() and FACEBOOK_CLIENT_SECRET.strip())
    if FACEBOOK_OAUTH_ENABLED:
        try:
            # Unregister first if exists
            if "facebook" in oauth._clients:
                del oauth._clients["facebook"]
            oauth.register(
                name="facebook",
                client_id=FACEBOOK_CLIENT_ID,
                client_secret=FACEBOOK_CLIENT_SECRET,
                access_token_url="https://graph.facebook.com/v19.0/oauth/access_token",
                authorize_url="https://www.facebook.com/v19.0/dialog/oauth",
                api_base_url="https://graph.facebook.com/v19.0/",
                client_kwargs={"scope": "email"},
            )
        except (KeyError, AttributeError):
            # If _clients doesn't exist or key doesn't exist, just register
            try:
                oauth.register(
                    name="facebook",
                    client_id=FACEBOOK_CLIENT_ID,
                    client_secret=FACEBOOK_CLIENT_SECRET,
                    access_token_url="https://graph.facebook.com/v19.0/oauth/access_token",
                    authorize_url="https://www.facebook.com/v19.0/dialog/oauth",
                    api_base_url="https://graph.facebook.com/v19.0/",
                    client_kwargs={"scope": "email"},
                )
            except Exception as e:
                print(f"Error registering Facebook OAuth: {e}")
                FACEBOOK_OAUTH_ENABLED = False
        except Exception as e:
            print(f"Error registering Facebook OAuth: {e}")
            FACEBOOK_OAUTH_ENABLED = False
    else:
        FACEBOOK_OAUTH_ENABLED = False

# Initial OAuth setup
GOOGLE_OAUTH_ENABLED = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)
if GOOGLE_OAUTH_ENABLED:
    oauth.register(
        name="google",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

FACEBOOK_OAUTH_ENABLED = bool(FACEBOOK_CLIENT_ID and FACEBOOK_CLIENT_SECRET)
if FACEBOOK_OAUTH_ENABLED:
    oauth.register(
        name="facebook",
        client_id=FACEBOOK_CLIENT_ID,
        client_secret=FACEBOOK_CLIENT_SECRET,
        access_token_url="https://graph.facebook.com/v19.0/oauth/access_token",
        authorize_url="https://www.facebook.com/v19.0/dialog/oauth",
        api_base_url="https://graph.facebook.com/v19.0/",
        client_kwargs={"scope": "email"},
    )

# ==== DB Init ====
def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS trial_emails (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            is_verified BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            consented BOOLEAN DEFAULT FALSE
        )
    """)
    # Backfill-safe migration: add column if it doesn't exist
    try:
        cur.execute("ALTER TABLE trial_emails ADD COLUMN IF NOT EXISTS consented BOOLEAN DEFAULT FALSE")
    except Exception:
        pass
    
    # Create page_settings table for admin panel
    cur.execute("""
        CREATE TABLE IF NOT EXISTS page_settings (
            id SERIAL PRIMARY KEY,
            setting_key TEXT UNIQUE NOT NULL,
            setting_value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Insert default settings if they don't exist
    default_settings = [
        ('google_login_enabled', 'true'),
        ('facebook_login_enabled', 'false'),
        ('background_image', 'url(../img/nuanu.png)'),
        ('background_image_type', 'url'),
        ('background_image_data', ''),
        ('background_color', '#667eea'),
        ('page_title', 'Welcome To NUANU Free WiFi'),
        ('button_text', 'Connect to WiFi')
    ]
    
    for key, value in default_settings:
        cur.execute("""
            INSERT INTO page_settings (setting_key, setting_value)
            VALUES (%s, %s)
            ON CONFLICT (setting_key) DO NOTHING
        """, (key, value))
    
    # Create scheduled_ads table for CMS scheduler
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_ads (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            background_image TEXT,
            background_image_type TEXT DEFAULT 'url',
            background_image_data TEXT,
            background_color TEXT DEFAULT '#667eea',
            page_title TEXT,
            button_text TEXT,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            start_time TIME DEFAULT '00:00:00',
            end_time TIME DEFAULT '23:59:59',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by TEXT,
            CHECK (end_date >= start_date)
        )
    """)
    
    # Create index for faster date queries
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_scheduled_ads_dates 
        ON scheduled_ads(start_date, end_date, is_active)
    """)
    
    conn.commit()
    cur.close()
    conn.close()

def get_page_settings():
    """Retrieve all page settings as a dictionary"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT setting_key, setting_value FROM page_settings")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {key: value for key, value in rows}

def get_active_scheduled_ad():
    """Get the currently active scheduled ad based on current date/time"""
    from datetime import datetime, time
    
    try:
        conn = None
        cur = None
        
        try:
            conn = get_connection()
            # Check if we're using SQLite (fallback) or PostgreSQL
            is_sqlite = isinstance(conn, sqlite3.Connection) if 'sqlite3' in globals() else False
            
            if is_sqlite:
                # SQLite fallback implementation
                return None
                
            # PostgreSQL implementation
            cur = conn.cursor()
            now = datetime.now()
            current_date = now.date()
            current_time = now.time()
            
            # Find active scheduled ad that matches current date and time
            query = """
                SELECT id, title, description, background_image, background_image_type, 
                       background_image_data, background_color, page_title, button_text,
                       start_date, end_date, start_time, end_time
                FROM scheduled_ads
                WHERE is_active = TRUE
                  AND start_date <= %s
                  AND end_date >= %s
                  AND (
                    (start_date < %s AND end_date > %s) OR
                    (start_date = %s AND start_time <= %s AND end_date > %s) OR
                    (start_date < %s AND end_date = %s AND end_time >= %s) OR
                    (start_date = %s AND end_date = %s AND start_time <= %s AND end_time >= %s)
                  )
                ORDER BY start_date DESC, start_time DESC
                LIMIT 1
            """
            
            params = (
                current_date, current_date,  # start_date <= current_date, end_date >= current_date
                current_date, current_date,   # start_date < current_date, end_date > current_date
                current_date, current_time, current_date,  # start_date = current_date, start_time <= current_time, end_date > current_date
                current_date, current_date, current_time,  # start_date < current_date, end_date = current_date, end_time >= current_time
                current_date, current_date, current_time, current_time  # start_date = end_date = current_date, start_time <= current_time <= end_time
            )
            
            cur.execute(query, params)
            row = cur.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'background_image': row[3],
                    'background_image_type': row[4],
                    'background_image_data': row[5],
                    'background_color': row[6],
                    'page_title': row[7],
                    'button_text': row[8],
                    'start_date': row[9],
                    'end_date': row[10],
                    'start_time': row[11],
                    'end_time': row[12]
                }
                
        except Exception as e:
            print(f"Error in get_active_scheduled_ad: {str(e)}")
            if conn:
                conn.rollback()
            # Return a default ad or None if there's an error
            return {
                'id': 0,
                'title': 'Welcome to NUANU WiFi',
                'description': 'Please connect to our WiFi network',
                'background_image': None,
                'background_image_type': 'url',
                'background_image_data': '',
                'background_color': '#667eea',
                'page_title': 'Welcome to NUANU WiFi',
                'button_text': 'Connect to WiFi',
                'start_date': datetime.now().date(),
                'end_date': (datetime.now() + timedelta(days=365)).date(),
                'start_time': time(0, 0),
                'end_time': time(23, 59)
            }
            
        finally:
            if cur:
                cur.close()
            if conn and not is_sqlite:  # Don't close SQLite connection as it's in-memory
                conn.close()
                
    except Exception as e:
        print(f"Critical error in get_active_scheduled_ad: {str(e)}")
        return None
        
    return None
    return None

def extract_media_url(value: str) -> str:
    """Strip CSS url() wrapper and surrounding quotes from a value."""
    if not value:
        return ""
    cleaned = value.strip()
    if not cleaned:
        return ""
    if cleaned.startswith("url(") and cleaned.endswith(")"):
        cleaned = cleaned[4:-1].strip()
    if cleaned and ((cleaned[0] == cleaned[-1]) and cleaned[0] in ("'", '"')):
        cleaned = cleaned[1:-1]
    return cleaned

def build_ad_image_src(background_image: str, background_image_type: str, background_image_data: str) -> str:
    """
    Convert the stored background/ad image information into a direct image source (URL or data URI).
    This keeps compatibility with older records that stored CSS url(...) strings.
    """
    image_type = (background_image_type or "").lower()
    data_value = (background_image_data or "").strip()
    raw_value = (background_image or "").strip()

    if image_type == "upload" and data_value:
        # Prefer data URIs, but also handle legacy url(...) values.
        if data_value.startswith("data:"):
            return data_value
        return extract_media_url(data_value)

    if image_type == "url" and raw_value:
        return extract_media_url(raw_value)

    # Fallback for legacy data
    if data_value:
        if data_value.startswith("data:"):
            return data_value
        return extract_media_url(data_value)
    if raw_value:
        return extract_media_url(raw_value)
    return ""

def serialize_time_value(value):
    """Return a consistent string for date/time/database values."""
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, time):
        return value.strftime("%H:%M:%S")
    return str(value)

def get_all_scheduled_ads():
    """Get all scheduled ads for admin panel"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, title, description, start_date, end_date, start_time, end_time,
               is_active, created_at, created_by
        FROM scheduled_ads
        ORDER BY start_date DESC, start_time DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {
            'id': row[0],
            'title': row[1],
            'description': row[2],
            'start_date': row[3],
            'end_date': row[4],
            'start_time': row[5],
            'end_time': row[6],
            'is_active': row[7],
            'created_at': row[8],
            'created_by': row[9]
        }
        for row in rows
    ]

def update_page_setting(key: str, value: str):
    """Update a specific page setting"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE page_settings 
        SET setting_value = %s, updated_at = CURRENT_TIMESTAMP 
        WHERE setting_key = %s
    """, (value, key))
    conn.commit()
    cur.close()
    conn.close()

def update_env_file(updates: dict):
    """Update .env file with new values. Preserves existing keys and adds new ones."""
    env_file = ".env"
    env_vars = {}
    
    # Read existing .env file
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
    
    # Update with new values
    env_vars.update(updates)
    
    # Write back to .env file
    with open(env_file, "w", encoding="utf-8") as f:
        # Write in a consistent order
        order = [
            "BASE_URL", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET",
            "FACEBOOK_CLIENT_ID", "FACEBOOK_CLIENT_SECRET",
            "DASHBOARD_PASSWORD", "GATEWAY_IP", "HOTSPOT_USER",
            "HOTSPOT_PASS", "DST_URL", "SECRET_KEY"
        ]
        written = set()
        for key in order:
            if key in env_vars:
                f.write(f"{key}={env_vars[key]}\n")
                written.add(key)
        # Write any remaining keys
        for key, value in env_vars.items():
            if key not in written:
                f.write(f"{key}={value}\n")

@app.on_event("startup")
def startup_event():
    init_db()

# ==== Simpan Email Baru (Auto-Verified) ====
@app.post("/save_trial_email")
async def save_email(request: Request):
    data = await request.json()
    email = data.get("email")
    consent = data.get("consent")
    if not email:
        return {"status": "error", "message": "Invalid email"}
    if consent is not True:
        return JSONResponse({"status": "error", "message": "Consent required"}, status_code=400)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO trial_emails (email, is_verified, consented)
        VALUES (%s, TRUE, TRUE)
        ON CONFLICT (email) DO UPDATE SET is_verified = TRUE, consented = TRUE
    """, (email,))
    conn.commit()
    cur.close()
    conn.close()

    return {"status": "exists", "message": "Auto-verified"}

# ==== Cek Email (Always Verified if Saved) ====
@app.post("/check_email")
async def check_email(request: Request):
    data = await request.json()
    email = data.get("email")
    if not email:
        return {"status": "error", "message": "Invalid email"}

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT is_verified FROM trial_emails WHERE email = %s", (email,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row and row[0]:
        return {"status": "exists"}
    else:
        return {"status": "not_verified"}

# ==== Google Login ====
@app.get("/auth/google/login")
async def login_google(request: StarletteRequest):
    if not GOOGLE_OAUTH_ENABLED:
        return JSONResponse({"status": "error", "message": "Google login is not configured"}, status_code=503)
    
    # Use the EXACT hostname from the request (don't normalize)
    # This ensures the session cookie domain matches the redirect_uri domain
    # IMPORTANT: Make sure BOTH localhost:8000 AND 127.0.0.1:8000 are registered 
    # in Google Cloud Console as authorized redirect URIs
    scheme = request.url.scheme
    host = request.url.hostname  # Keep original hostname (localhost or 127.0.0.1)
    port = request.url.port
    
    # Build redirect_uri using the exact hostname from the request
    if port and port not in [80, 443]:
        base_url = f"{scheme}://{host}:{port}"
    else:
        base_url = f"{scheme}://{host}"
    redirect_uri = f"{base_url}/auth/google/callback"
    
    # Store redirect_uri in session to ensure we use the same one in callback
    request.session["oauth_redirect_uri"] = redirect_uri
    
    print(f"DEBUG: OAuth redirect_uri = {redirect_uri}, hostname = {host}")
    
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth/google/callback")
async def auth_google_callback(request: StarletteRequest):
    if not GOOGLE_OAUTH_ENABLED:
        return JSONResponse({"status": "error", "message": "Google login is not configured"}, status_code=503)
    
    try:
        # Use the stored redirect_uri from session (set during login_google)
        # This ensures we're using the exact same redirect_uri that was used initially
        stored_redirect_uri = request.session.get("oauth_redirect_uri")
        
        print(f"DEBUG: Callback received, stored_redirect_uri = {stored_redirect_uri}")
        print(f"DEBUG: Callback URL = {request.url}")
        print(f"DEBUG: Session keys = {list(request.session.keys())}")
        
        # Get the token - Authlib will verify the state parameter from the session
        # The state was stored in the session during authorize_redirect
        token = await oauth.google.authorize_access_token(request)
        
        # Authlib with OpenID Connect should automatically fetch userinfo
        # Check if userinfo is in token response
        user_info = token.get("userinfo")
        
        # If not in token, fetch it explicitly
        if not user_info:
            resp = await oauth.google.get("userinfo", token=token)
            user_info = resp.json()
        
        if not user_info:
            return JSONResponse({"status": "error", "message": "Failed to retrieve user information from Google"}, status_code=500)

        email = user_info.get("email")
        if not email:
            return JSONResponse({"status": "error", "message": "Google account did not provide an email address"}, status_code=400)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Google OAuth error: {error_details}")
        return JSONResponse({"status": "error", "message": f"Google authentication failed: {str(e)}"}, status_code=500)

    # Save or update in DB as verified
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO trial_emails (email, is_verified)
        VALUES (%s, TRUE)
        ON CONFLICT (email) DO UPDATE SET is_verified = TRUE
    """, (email,))
    conn.commit()
    cur.close()
    conn.close()

    login_url = (
        f"http://{GATEWAY_IP}/login?"
        f"username={HOTSPOT_USER}&password={HOTSPOT_PASS}&dst={DST_URL}"
    )
    return RedirectResponse(url=login_url)

# ==== Facebook Login ====
@app.get("/auth/facebook/login")
async def login_facebook(request: StarletteRequest):
    if not FACEBOOK_OAUTH_ENABLED:
        return JSONResponse({"status": "error", "message": "Facebook login is not configured"}, status_code=503)
    
    # Use the EXACT hostname from the request (same as Google)
    # IMPORTANT: Facebook requires HTTPS when "Enforce HTTPS" is enabled in Facebook Developer Console
    # For localhost testing, you must either:
    # 1. Disable "Enforce HTTPS" in Facebook Developer Console (Settings > OAuth Client Settings)
    # 2. Use HTTPS for localhost (requires SSL setup)
    # 3. Test Facebook login only on production (https://wifi.nuanu.io)
    scheme = request.url.scheme
    host = request.url.hostname
    port = request.url.port
    
    # Build redirect_uri using the exact hostname from the request
    if port and port not in [80, 443]:
        base_url = f"{scheme}://{host}:{port}"
    else:
        base_url = f"{scheme}://{host}"
    redirect_uri = f"{base_url}/auth/facebook/callback"
    
    # Store redirect_uri in session
    request.session["oauth_facebook_redirect_uri"] = redirect_uri
    
    print(f"DEBUG: Facebook OAuth redirect_uri = {redirect_uri}, hostname = {host}, scheme = {scheme}")
    
    # Warn if using HTTP with localhost (Facebook may reject this if HTTPS is enforced)
    if scheme == "http" and host in ["localhost", "127.0.0.1"]:
        print("WARNING: Facebook login with HTTP on localhost may fail if 'Enforce HTTPS' is enabled in Facebook Developer Console")
    
    return await oauth.facebook.authorize_redirect(request, redirect_uri)

@app.get("/auth/facebook/callback")
async def auth_facebook_callback(request: StarletteRequest):
    if not FACEBOOK_OAUTH_ENABLED:
        return JSONResponse({"status": "error", "message": "Facebook login is not configured"}, status_code=503)
    token = await oauth.facebook.authorize_access_token(request)
    user_resp = await oauth.facebook.get("me?fields=id,name,email", token=token)
    user_info = user_resp.json()
    email = user_info.get("email")
    if not email:
        return JSONResponse({"status": "error", "message": "Facebook account did not return an email address. Email scope is required."}, status_code=400)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO trial_emails (email, is_verified, consented)
        VALUES (%s, TRUE, TRUE)
        ON CONFLICT (email) DO UPDATE SET is_verified = TRUE, consented = TRUE
    """, (email,))
    conn.commit()
    cur.close()
    conn.close()

    login_url = (
        f"http://{GATEWAY_IP}/login?"
        f"username={HOTSPOT_USER}&password={HOTSPOT_PASS}&dst={DST_URL}"
    )
    return RedirectResponse(url=login_url)

# ==== Dashboard Login Page ====
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_login(request: Request):
    if request.session.get("logged_in"):
        # Get page parameter from query string, default to 1
        try:
            page = int(request.query_params.get("page", 1))
            if page < 1:
                page = 1
        except (ValueError, TypeError):
            page = 1
        # Pass-through filter params
        return await show_dashboard(
            page=page,
            date_filter=request.query_params.get("date_filter"),
            start_date_str=request.query_params.get("start_date"),
            end_date_str=request.query_params.get("end_date"),
        )
    
    html = """
    <html>   <head>
        <title>Dashboard Login</title>
        <style>
          body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea, #764ba2);
            display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0;
          }
          .login-box {
            background: white; padding: 40px; border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2); text-align: center; width: 300px;
          }
          input[type=password] { width: 100%; padding: 12px 10px; margin: 15px 0; border-radius: 6px; border: 1px solid #ccc; font-size: 16px; }
          button { background: #667eea; color: white; border: none; padding: 12px 20px; border-radius: 6px; cursor: pointer; font-size: 16px; }
          button:hover { background: #5a67d8; }
        </style>
      </head>
      <body>
        <div class="login-box">
          <h2>🔒 Dashboard Login</h2>
          <form method="post" action="/dashboard">
            <input type="password" name="password" placeholder="Enter password" required>
            <button type="submit">Login</button>
          </form>
        </div>
      </body>
    </html>
    """
    return HTMLResponse(content=html)

# ==== Handle Dashboard Login ====
# ==== Handle Dashboard Login ====
@app.post("/dashboard", response_class=HTMLResponse)
async def dashboard_post(request: Request, password: str = Form(...)):
    if password != DASHBOARD_PASSWORD:
        return HTMLResponse(content="<h2>❌ Invalid password</h2><a href='/dashboard'>Try again</a>", status_code=401)

    request.session["logged_in"] = True
    # Get page parameter from query string, default to 1
    try:
        page = int(request.query_params.get("page", 1))
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        page = 1
    return await show_dashboard(page=page)

# ==== Show Dashboard ====
def _compute_date_range(
    date_filter: Optional[str], start_date_str: Optional[str], end_date_str: Optional[str]
) -> Tuple[Optional[datetime], Optional[datetime], str]:
    """Compute start and end datetime based on filter preset or custom fields.
    Returns (start_dt, end_dt, human_label).
    """
    today = date.today()

    def start_of_month(d: date) -> date:
        return d.replace(day=1)

    def end_of_month(d: date) -> date:
        next_month = (d.replace(day=28) + timedelta(days=4)).replace(day=1)
        return next_month - timedelta(days=1)

    if date_filter == "today":
        start_dt = datetime.combine(today, datetime.min.time())
        end_dt = datetime.combine(today, datetime.max.time())
        return start_dt, end_dt, "Today"
    if date_filter == "yesterday":
        y = today - timedelta(days=1)
        start_dt = datetime.combine(y, datetime.min.time())
        end_dt = datetime.combine(y, datetime.max.time())
        return start_dt, end_dt, "Yesterday"
    if date_filter == "last7":
        start_dt = datetime.combine(today - timedelta(days=6), datetime.min.time())
        end_dt = datetime.combine(today, datetime.max.time())
        return start_dt, end_dt, "Last 7 days"
    if date_filter == "last30":
        start_dt = datetime.combine(today - timedelta(days=29), datetime.min.time())
        end_dt = datetime.combine(today, datetime.max.time())
        return start_dt, end_dt, "Last 30 days"
    if date_filter == "thisMonth":
        s = start_of_month(today)
        e = end_of_month(today)
        return datetime.combine(s, datetime.min.time()), datetime.combine(e, datetime.max.time()), "This month"
    if date_filter == "prevMonth":
        first_this = start_of_month(today)
        prev_end = first_this - timedelta(days=1)
        prev_start = start_of_month(prev_end)
        return (
            datetime.combine(prev_start, datetime.min.time()),
            datetime.combine(prev_end, datetime.max.time()),
            "Previous month",
        )

    # custom or none
    if start_date_str and end_date_str:
        try:
            s_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            e_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            start_dt = datetime.combine(s_date, datetime.min.time())
            end_dt = datetime.combine(e_date, datetime.max.time())
            return start_dt, end_dt, f"{s_date.isoformat()} → {e_date.isoformat()}"
        except Exception:
            pass

    return None, None, "All time"

async def show_dashboard(page: int = 1, page_size: int = 20, date_filter: Optional[str] = None, start_date_str: Optional[str] = None, end_date_str: Optional[str] = None):
    conn = get_connection()
    cur = conn.cursor()
    
    # Build WHERE clause from date filter
    start_dt, end_dt, range_label = _compute_date_range(date_filter, start_date_str, end_date_str)
    where_sql = ""
    params: List = []
    if start_dt and end_dt:
        where_sql = "WHERE created_at BETWEEN %s AND %s"
        params.extend([start_dt, end_dt])

    # Get total count for pagination
    cur.execute(f"SELECT COUNT(*) FROM trial_emails {where_sql}", params)
    total_count = cur.fetchone()[0]
    
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Get paginated results
    cur.execute(
        f"""
        SELECT email, created_at 
        FROM trial_emails 
        {where_sql}
        ORDER BY created_at DESC 
        LIMIT %s OFFSET %s
    """,
        (*params, page_size, offset),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    # Calculate pagination info
    total_pages = (total_count + page_size - 1) // page_size
    has_prev = page > 1
    has_next = page < total_pages

    # Build filter query string for pagination links
    filter_qs = ""
    if date_filter:
        filter_qs += f"&date_filter={date_filter}"
    if start_date_str:
        filter_qs += f"&start_date={start_date_str}"
    if end_date_str:
        filter_qs += f"&end_date={end_date_str}"

    html = f"""
    <html>
      <head>
        <title>Email Dashboard</title>
        <style>
          body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f3f4f6; padding: 20px; }}
          h1 {{ text-align: center; color: #333; }}
          .filters {{ background: white; border-radius: 8px; padding: 16px; box-shadow: 0 5px 15px rgba(0,0,0,0.08); }}
          .filters form {{ display: flex; flex-wrap: wrap; gap: 12px; align-items: end; }}
          .filters label {{ font-size: 13px; color: #555; }}
          .filters select, .filters input[type=date] {{ padding: 8px 10px; border: 1px solid #ccc; border-radius: 6px; }}
          .filters button {{ background: #4f46e5; color: white; border: none; padding: 10px 14px; border-radius: 6px; cursor: pointer; }}
          .pagination-info {{ text-align: center; margin: 10px 0; color: #666; font-size: 14px; }}
          table {{ width: 100%; border-collapse: collapse; margin-top: 20px; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
          th, td {{ padding: 12px 15px; text-align: left; }}
          th {{ background: #667eea; color: white; }}
          tr:nth-child(even) {{ background: #f2f2f2; }}
          .logout, .download {{ display: inline-block; margin: 10px; text-decoration: none; font-weight: bold; padding: 10px 15px; border-radius: 6px; }}
          .logout {{ color: #667eea; border: 1px solid #667eea; }}
          .logout:hover {{ background: #667eea; color: white; }}
          .download {{ background: #10b981; color: white; }}
          .download:hover {{ background: #059669; }}
          .buttons {{ text-align:center; margin-top: 20px; }}
          .pagination {{ text-align: center; margin: 20px 0; }}
          .pagination a {{ display: inline-block; padding: 8px 12px; margin: 0 4px; text-decoration: none; border: 1px solid #667eea; border-radius: 4px; color: #667eea; }}
          .pagination a:hover {{ background: #667eea; color: white; }}
          .pagination .current {{ background: #667eea; color: white; }}
          .pagination .disabled {{ color: #ccc; border-color: #ccc; cursor: not-allowed; }}
          .pagination .disabled:hover {{ background: transparent; color: #ccc; }}
          @media(max-width: 600px) {{ table, th, td {{ font-size: 14px; }} }}
        </style>
      </head>
      <body>
        <h1>📊 Collected Emails</h1>
        <div class="filters">
          <form method="get" action="/dashboard">
            <div>
              <label for="date_filter">Date</label><br>
              <select name="date_filter" id="date_filter">
                <option value="" {"selected" if not date_filter else ""}>All time</option>
                <option value="today" {"selected" if date_filter=="today" else ""}>Today</option>
                <option value="yesterday" {"selected" if date_filter=="yesterday" else ""}>Yesterday</option>
                <option value="last7" {"selected" if date_filter=="last7" else ""}>Last 7 days</option>
                <option value="last30" {"selected" if date_filter=="last30" else ""}>Last 30 days</option>
                <option value="thisMonth" {"selected" if date_filter=="thisMonth" else ""}>This month</option>
                <option value="prevMonth" {"selected" if date_filter=="prevMonth" else ""}>Previous month</option>
                <option value="custom" {"selected" if date_filter=="custom" else ""}>Custom range</option>
              </select>
            </div>
            <div>
              <label for="start_date">Start</label><br>
              <input type="date" name="start_date" id="start_date" value="{start_date_str or ''}">
            </div>
            <div>
              <label for="end_date">End</label><br>
              <input type="date" name="end_date" id="end_date" value="{end_date_str or ''}">
            </div>
            <div>
              <input type="hidden" name="page" value="1">
              <button type="submit">Apply</button>
            </div>
          </form>
          <div style="margin-top:8px;color:#666;font-size:13px;">Range: {range_label}</div>
        </div>
        <div class="pagination-info">
          Showing {len(rows)} of {total_count} emails (Page {page} of {total_pages})
        </div>
        <table>
          <tr><th>Email</th><th>Created At</th></tr>
    """
    for email, created_at in rows:
        html += f"<tr><td>{email}</td><td>{created_at.date()}</td></tr>"

    # Add pagination controls
    html += """
        </table>
        <div class="pagination">
    """
    
    # Previous button
    if has_prev:
        html += f'<a href="/dashboard?page={page-1}{filter_qs}">« Previous</a>'
    else:
        html += '<span class="disabled">« Previous</span>'
    
    # Page numbers (show up to 5 pages around current page)
    start_page = max(1, page - 2)
    end_page = min(total_pages, page + 2)
    
    if start_page > 1:
        html += f'<a href="/dashboard?page=1{filter_qs}">1</a>'
        if start_page > 2:
            html += '<span>...</span>'
    
    for p in range(start_page, end_page + 1):
        if p == page:
            html += f'<span class="current">{p}</span>'
        else:
            html += f'<a href="/dashboard?page={p}{filter_qs}">{p}</a>'
    
    if end_page < total_pages:
        if end_page < total_pages - 1:
            html += '<span>...</span>'
        html += f'<a href="/dashboard?page={total_pages}{filter_qs}">{total_pages}</a>'
    
    # Next button
    if has_next:
        html += f'<a href="/dashboard?page={page+1}{filter_qs}">Next »</a>'
    else:
        html += '<span class="disabled">Next »</span>'
    
    html += """
        </div>
        <div class="buttons">
            <a href="/admin" class="download" style="text-decoration:none;">⚙️ Admin Panel</a>
            <form method="get" action="/dashboard/export" style="display:inline-block;margin:10px;">
                <input type="hidden" name="date_filter" value="{date_filter or ''}">
                <input type="hidden" name="start_date" value="{start_date_str or ''}">
                <input type="hidden" name="end_date" value="{end_date_str or ''}">
                <label style="margin-right:6px;">Format:</label>
                <label><input type="radio" name="format" value="csv" checked> CSV</label>
                <label><input type="radio" name="format" value="xlsx"> XLSX</label>
                <label><input type="radio" name="format" value="pdf"> PDF</label>
                <button class="download" type="submit">Download</button>
            </form>
            <a href="/dashboard/logout" class="logout">Logout</a>
        </div>
      </body>
    </html>
    """
    return HTMLResponse(content=html)

# ==== Dashboard Logout ====
@app.get("/dashboard/logout")
async def dashboard_logout(request: Request):
    request.session.clear()
    return RedirectResponse("/dashboard")

# ==== Export by Date and Format ====
@app.get("/dashboard/export")
async def export_data(request: Request):
    if not request.session.get("logged_in"):
        return RedirectResponse("/dashboard")

    qp = request.query_params
    fmt = (qp.get("format") or "csv").lower()
    date_filter = qp.get("date_filter")
    start_date_str = qp.get("start_date")
    end_date_str = qp.get("end_date")

    start_dt, end_dt, _ = _compute_date_range(date_filter, start_date_str, end_date_str)

    conn = get_connection()
    cur = conn.cursor()
    params: List = []
    where_sql = ""
    if start_dt and end_dt:
        where_sql = "WHERE created_at BETWEEN %s AND %s"
        params.extend([start_dt, end_dt])
    cur.execute(
        f"SELECT email, created_at FROM trial_emails {where_sql} ORDER BY created_at DESC",
        params,
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    # CSV
    if fmt == "csv":
        csv_file = StringIO()
        writer = csv.writer(csv_file)
        writer.writerow(["Email", "Created At"])
        for email, created_at in rows:
            writer.writerow([email, created_at.date()])
        csv_file.seek(0)
        fname = "emails.csv"
        if start_dt and end_dt:
            fname = f"emails_{start_dt.date().isoformat()}_{end_dt.date().isoformat()}.csv"
        return StreamingResponse(
            csv_file,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={fname}"},
        )

    # XLSX
    if fmt == "xlsx":
        if Workbook is None:
            return JSONResponse({"error": "XLSX export requires openpyxl to be installed"}, status_code=500)
        wb = Workbook()
        ws = wb.active
        ws.title = "Emails"
        ws.append(["Email", "Created At"])
        for email, created_at in rows:
            ws.append([email, created_at.date().isoformat()])
        bio = BytesIO()
        wb.save(bio)
        bio.seek(0)
        fname = "emails.xlsx"
        if start_dt and end_dt:
            fname = f"emails_{start_dt.date().isoformat()}_{end_dt.date().isoformat()}.xlsx"
        return StreamingResponse(
            bio,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={fname}"},
        )

    # PDF
    if fmt == "pdf":
        if SimpleDocTemplate is None:
            return JSONResponse({"error": "PDF export requires reportlab to be installed"}, status_code=500)
        bio = BytesIO()
        doc = SimpleDocTemplate(bio, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        title = Paragraph("Collected Emails", styles["Title"])
        elements.append(title)
        elements.append(Spacer(1, 12))
        data = [["Email", "Created At"]] + [[e, c.date().isoformat()] for e, c in rows]
        table = Table(data, colWidths=[350, 150])
        table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#667eea")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor("#f2f2f2")]),
            ])
        )
        elements.append(table)
        doc.build(elements)
        bio.seek(0)
        fname = "emails.pdf"
        if start_dt and end_dt:
            fname = f"emails_{start_dt.date().isoformat()}_{end_dt.date().isoformat()}.pdf"
        return StreamingResponse(
            bio,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={fname}"},
        )

    return JSONResponse({"error": "Unsupported format"}, status_code=400)

# ==== CMS Scheduler Management Page ====
@app.get("/admin/scheduler", response_class=HTMLResponse)
async def scheduler_page(request: Request):
    if not request.session.get("logged_in"):
        return RedirectResponse("/dashboard")
    
    ads = get_all_scheduled_ads()
    active_ad = get_active_scheduled_ad()
    
    html = f"""
    <html>
      <head>
        <title>CMS Scheduler - WiFi Login</title>
        <style>
          body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea, #764ba2);
            padding: 20px;
            margin: 0;
          }}
          .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
          }}
          .nav-links {{
            margin-bottom: 20px;
          }}
          .nav-links a {{
            color: #667eea;
            text-decoration: none;
            margin-right: 15px;
            font-weight: 600;
          }}
          .nav-links a:hover {{
            text-decoration: underline;
          }}
          h1 {{
            color: #333;
            margin-bottom: 10px;
          }}
          .subtitle {{
            color: #666;
            margin-bottom: 30px;
          }}
          .active-now-badge {{
            background: #10b981;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            display: inline-block;
            margin-left: 10px;
            animation: pulse 2s infinite;
          }}
          @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.7; }}
          }}
          .pending-badge {{
            background: #f59e0b;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            display: inline-block;
            margin-left: 10px;
          }}
          .inactive-badge {{
            background: #6b7280;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            display: inline-block;
            margin-left: 10px;
          }}
          .btn {{
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            margin: 5px;
          }}
          .btn:hover {{
            background: #5a67d8;
          }}
          .btn-danger {{
            background: #dc3545;
          }}
          .btn-danger:hover {{
            background: #c82333;
          }}
          .btn-success {{
            background: #10b981;
          }}
          .btn-success:hover {{
            background: #059669;
          }}
          table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background: white;
          }}
          th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e1e8ed;
          }}
          th {{
            background: #667eea;
            color: white;
            font-weight: 600;
          }}
          tr:hover {{
            background: #f8f9fa;
          }}
          .modal {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.7);
            z-index: 1000;
            overflow-y: auto;
          }}
          .modal.active {{
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
          }}
          .modal-content {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            max-width: 600px;
            width: 100%;
            max-height: 90vh;
            overflow-y: auto;
          }}
          .form-group {{
            margin-bottom: 20px;
          }}
          .form-group label {{
            display: block;
            font-weight: 600;
            margin-bottom: 8px;
            color: #333;
          }}
          .ad-image-uploader {{
            border: 2px dashed #cbd5f5;
            border-radius: 12px;
            padding: 16px;
            background: #f8f9ff;
          }}
          .ad-source-tabs {{
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
          }}
          .ad-tab {{
            flex: 1;
            border: none;
            padding: 10px 12px;
            border-radius: 8px;
            background: white;
            font-weight: 600;
            cursor: pointer;
            border: 1px solid #d1d8ff;
            color: #4b5563;
          }}
          .ad-tab.active {{
            background: #667eea;
            color: white;
            border-color: #667eea;
          }}
          .ad-source-panel {{
            margin-bottom: 15px;
          }}
          .ad-source-panel.hidden {{
            display: none;
          }}
          .helper-text {{
            font-size: 12px;
            color: #6b7280;
            margin-top: 8px;
          }}
          /* Custom Notification Modal */
          .notification-modal {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.6);
            backdrop-filter: blur(4px);
            z-index: 9999;
            align-items: center;
            justify-content: center;
          }}
          .notification-modal.active {{
            display: flex;
            animation: fadeIn 0.2s ease;
          }}
          .notification-content {{
            background: white;
            border-radius: 16px;
            padding: 32px;
            max-width: 480px;
            width: 90%;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            text-align: center;
            animation: slideIn 0.3s ease;
          }}
          .notification-icon {{
            font-size: 48px;
            margin-bottom: 16px;
          }}
          .notification-icon.error {{
            color: #dc3545;
          }}
          .notification-icon.success {{
            color: #10b981;
          }}
          .notification-title {{
            font-size: 20px;
            font-weight: 700;
            color: #333;
            margin-bottom: 12px;
          }}
          .notification-message {{
            font-size: 15px;
            color: #666;
            line-height: 1.6;
            margin-bottom: 24px;
          }}
          .notification-btn {{
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 32px;
            border-radius: 8px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
          }}
          .notification-btn:hover {{
            background: #5a67d8;
            transform: translateY(-1px);
          }}
          @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
          }}
          @keyframes slideIn {{
            from {{ transform: translateY(-20px); opacity: 0; }}
            to {{ transform: translateY(0); opacity: 1; }}
          }}
          .ad-preview {{
            border: 1px dashed #a5b4fc;
            border-radius: 12px;
            padding: 12px;
            background: white;
            min-height: 160px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
          }}
          .ad-preview img {{
            max-width: 100%;
            border-radius: 8px;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.2);
          }}
          .hidden {{
            display: none !important;
          }}
          .form-row {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
          }}
          .empty-state {{
            text-align: center;
            padding: 60px 20px;
            color: #666;
          }}
          .empty-state h3 {{
            color: #333;
            margin-bottom: 10px;
          }}
        </style>
      </head>
      <body>
        <div class="container">
          <div class="nav-links">
            <a href="/dashboard">← Back to Dashboard</a>
            <a href="/admin">⚙️ Admin Panel</a>
            <a href="/login" target="_blank">Preview Login Page →</a>
          </div>
          
          <h1>📅 CMS Scheduler</h1>
          <p class="subtitle">Schedule Advertisements</p>
          
          {f'<div style="background: #dcfce7; padding: 15px; border-radius: 8px; margin-bottom: 20px;"><strong>Currently Active:</strong> {active_ad["title"]} (until {active_ad["end_date"]})</div>' if active_ad else ''}
          
          <button class="btn btn-success" id="create-schedule-btn">➕ Create New Schedule</button>
          
          <table>
            <thead>
              <tr>
                <th>Title</th>
                <th>Start Date/Time</th>
                <th>End Date/Time</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
    """
    
    if not ads:
        html += """
              <tr>
                <td colspan="5" class="empty-state">
                  <h3>No scheduled ads yet</h3>
                  <p>Click "Create New Schedule" to add your first scheduled ad</p>
                </td>
              </tr>
        """
    else:
        for ad in ads:
            # Determine status based on dates and active flag
            from datetime import datetime
            now = datetime.now()
            current_date = now.date()
            start_date = ad['start_date']
            end_date = ad['end_date']
            if ad['is_active'] and start_date <= current_date <= end_date:
                status_badge = '<span class="active-now-badge">ACTIVE NOW</span>'
            elif current_date < start_date:
                status_badge = '<span class="pending-badge">PENDING</span>'
            elif current_date > end_date:
                status_badge = '<span class="inactive-badge">EXPIRED</span>'
            else:
                status_badge = '<span class="pending-badge">PENDING</span>'
            html += f"""
              <tr>
                <td><strong>{ad['title']}</strong></td>
                <td>{ad['start_date']} {ad['start_time']}</td>
                <td>{ad['end_date']} {ad['end_time']}</td>
                <td>{status_badge}</td>
                <td>
                  <button class="btn" onclick="editAd({ad['id']})">✏️ Edit</button>
                  <button class="btn btn-danger" onclick="deleteAd({ad['id']})">🗑️ Delete</button>
                </td>
              </tr>
            """
    
    html += """
            </tbody>
          </table>
        </div>
        
        <!-- Create/Edit Modal -->
        <div id="adModal" class="modal">
          <div class="modal-content">
            <h2 id="modalTitle">Create New Schedule</h2>
            <form id="adForm">
              <input type="hidden" id="adId">
              <div class="form-group">
                <label>Title *</label>
                <input type="text" id="title" required>
              </div>
              <div class="form-group">
                <label>Description</label>
                <textarea id="description"></textarea>
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label>Start Date (DD/MM/YYYY) *</label>
                  <input type="text" id="start_date" placeholder="dd/mm/yyyy" required>
                </div>
                <div class="form-group">
                  <label>End Date (DD/MM/YYYY) *</label>
                  <input type="text" id="end_date" placeholder="dd/mm/yyyy" required>
                </div>
                <script src="https://cdn.jsdelivr.net/npm/flatpickr"></script>
                <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css">
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label>Start Time</label>
                  <input type="time" id="start_time" value="00:00">
                </div>
                <div class="form-group">
                  <label>End Time</label>
                  <input type="time" id="end_time" value="23:59">
                </div>
              </div>
              <div class="form-group">
                <label>Advertisement Image *</label>
                <div class="ad-image-uploader">
                  <div class="ad-source-tabs">
                    <button type="button" class="ad-tab active" id="upload-device-btn" data-source="upload">Upload from device</button>
                    <button type="button" class="ad-tab" id="use-url-btn" data-source="url">Use image URL</button>
                  </div>
                  <div class="ad-source-panel" data-panel="upload">
                    <input type="file" id="adImageFile" accept="image/*">
                    <p class="helper-text">Choose a JPG, PNG, or WebP from your computer or phone. Recommended size 1080 × 1350 px.</p>
                  </div>
                  <div class="ad-source-panel hidden" data-panel="url">
                    <input type="url" id="adImageUrl" placeholder="https://example.com/promo.jpg">
                    <p class="helper-text">Make sure the link is publicly accessible.</p>
                  </div>
                  <div class="ad-preview" id="adImagePreview">
                    <p class="helper-text">No image selected yet.</p>
                  </div>
                </div>
              </div>
              <div style="margin-top: 20px;">
                <button type="submit" class="btn btn-success">💾 Save</button>
                <button type="button" class="btn" onclick="closeModal()">Cancel</button>
              </div>
            </form>
          </div>
        </div>

        <!-- Delete Confirmation Modal -->
        <div id="deleteConfirmModal" class="modal">
          <div class="modal-content" style="max-width: 420px; text-align: center;">
            <h2>Delete Schedule</h2>
            <p style="margin-top: 10px; color: #374151;">
              Are you sure you want to Delete this?
            </p>
            <div style="margin-top: 24px; display: flex; justify-content: center; gap: 12px;">
              <button type="button" class="btn btn-danger" id="confirmDeleteYes">Yes</button>
              <button type="button" class="btn" id="confirmDeleteNo">No</button>
            </div>
          </div>
        </div>

        <!-- Notification Modal (replaces alert()) -->
        <div id="notificationModal" class="notification-modal">
          <div class="notification-content">
            <div class="notification-icon" id="notificationIcon">⚠️</div>
            <h3 class="notification-title" id="notificationTitle">Notification</h3>
            <p class="notification-message" id="notificationMessage"></p>
            <button class="notification-btn" onclick="closeNotification()">OK</button>
          </div>
        </div>

        <script>
          document.addEventListener('DOMContentLoaded', function() {
            // Global variables for image handling
            let imageType = 'upload'; // 'upload' or 'url'
            let imageData = '';       // For base64 data when uploading
            let imageUrl = '';        // For URL when using external image

            // Delete confirmation state
            let pendingDeleteId = null;
            const deleteModal = document.getElementById('deleteConfirmModal');
            const confirmDeleteYes = document.getElementById('confirmDeleteYes');
            const confirmDeleteNo = document.getElementById('confirmDeleteNo');
            
            // Notification Modal Functions
            function showNotification(message, type = 'error') {{
              const modal = document.getElementById('notificationModal');
              const icon = document.getElementById('notificationIcon');
              const title = document.getElementById('notificationTitle');
              const messageEl = document.getElementById('notificationMessage');
              
              if (type === 'error') {{
                icon.textContent = '❌';
                icon.className = 'notification-icon error';
                title.textContent = 'Error';
              }} else if (type === 'success') {{
                icon.textContent = '✅';
                icon.className = 'notification-icon success';
                title.textContent = 'Success';
              }} else {{
                icon.textContent = '⚠️';
                icon.className = 'notification-icon';
                title.textContent = 'Notification';
              }}
              
              messageEl.textContent = message;
              modal.classList.add('active');
            }}
            
            window.closeNotification = function() {{
              const modal = document.getElementById('notificationModal');
              modal.classList.remove('active');
            }};
            
            // DOM Elements
            const modal = document.getElementById('adModal');
            const createBtn = document.getElementById('create-schedule-btn');
            const form = document.getElementById('adForm');
            const titleInput = document.getElementById('title');
            const descriptionInput = document.getElementById('description');
            const startDateInput = document.getElementById('start_date');
            const endDateInput = document.getElementById('end_date');
            const startTimeInput = document.getElementById('start_time');
            const endTimeInput = document.getElementById('end_time');
            const imageFileInput = document.getElementById('adImageFile');
            const imagePreview = document.getElementById('adImagePreview');
            const uploadDeviceBtn = document.getElementById('upload-device-btn');
            const useUrlBtn = document.getElementById('use-url-btn');
            const uploadPanel = document.querySelector('.ad-source-panel[data-panel="upload"]');
            const urlPanel = document.querySelector('.ad-source-panel[data-panel="url"]');
            const imageUrlInput = document.getElementById('adImageUrl');

            function openCreateModal() {
              if (!modal) return;
              modal.classList.add('active');
            }

            function closeModal() {
              if (!modal) return;
              modal.classList.remove('active');
            }

            // Helper to toggle between upload and URL panels
            function showUploadPanel() {
              if (uploadDeviceBtn) uploadDeviceBtn.classList.add('active');
              if (useUrlBtn) useUrlBtn.classList.remove('active');
              if (uploadPanel) uploadPanel.classList.remove('hidden');
              if (urlPanel) urlPanel.classList.add('hidden');
            }

            function showUrlPanel() {
              if (uploadDeviceBtn) uploadDeviceBtn.classList.remove('active');
              if (useUrlBtn) useUrlBtn.classList.add('active');
              if (uploadPanel) uploadPanel.classList.add('hidden');
              if (urlPanel) urlPanel.classList.remove('hidden');
            }

            // Basic preview for "Upload from device" and store data
            if (imageFileInput && imagePreview) {
              imageFileInput.addEventListener('change', function(e) {
                const file = e.target.files[0];
                if (!file) {
                  imagePreview.innerHTML = '<p class=\"helper-text\">No image selected yet.</p>';
                  return;
                }
                if (!file.type.startsWith('image/')) {
                  showNotification('Please choose an image file.', 'error');
                  e.target.value = '';
                  return;
                }
                const reader = new FileReader();
                reader.onload = function(ev) {
                  imageType = 'upload';
                  imageData = ev.target.result;
                  imageUrl = '';
                  const img = document.createElement('img');
                  img.src = ev.target.result;
                  img.alt = 'Advertisement preview';
                  imagePreview.innerHTML = '';
                  imagePreview.appendChild(img);
                };
                reader.readAsDataURL(file);
              });
            }

            // When clicking "Upload from device", switch panel AND open file picker
            if (uploadDeviceBtn) {
              uploadDeviceBtn.addEventListener('click', function(e) {
                e.preventDefault();
                showUploadPanel();
                if (imageFileInput) {
                  imageFileInput.click();
                }
              });
            }

            // When clicking "Use image URL", just switch to URL panel
            if (useUrlBtn) {
              useUrlBtn.addEventListener('click', function(e) {
                e.preventDefault();
                showUrlPanel();
                if (imageUrlInput) {
                  imageUrl = imageUrlInput.value.trim();
                  imageType = 'url';
                }
              });
            }

            // Ensure initial state is upload panel
            showUploadPanel();

            if (createBtn) {
              createBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                openCreateModal();
              });
            }

            // Initialize date pickers
            document.addEventListener('DOMContentLoaded', function() {
              flatpickr("#start_date", {
                dateFormat: "d/m/Y",
                allowInput: true,
                onChange: function(selectedDates, dateStr, instance) {
                  // Ensure the date is in the correct format when selected
                  if (dateStr) {
                    instance.input.value = dateStr;
                  }
                }
              });
              
              flatpickr("#end_date", {
                dateFormat: "d/m/Y",
                allowInput: true,
                onChange: function(selectedDates, dateStr, instance) {
                  // Ensure the date is in the correct format when selected
                  if (dateStr) {
                    instance.input.value = dateStr;
                  }
                }
              });
            });
            
            // Function to format date to DD/MM/YYYY
            function formatDateForDisplay(dateString) {
              if (!dateString) return '';
              // If already in DD/MM/YYYY format, return as is
              if (/^\d{2}\/\d{2}\/\d{4}$/.test(dateString)) {
                return dateString;
              }
              // Try to parse as YYYY-MM-DD (ISO format)
              const date = new Date(dateString);
              if (!isNaN(date.getTime())) {
                const day = String(date.getDate()).padStart(2, '0');
                const month = String(date.getMonth() + 1).padStart(2, '0');
                const year = date.getFullYear();
                return `${day}/${month}/${year}`;
              }
              return dateString; // Return original if can't parse
            }

            // Function to convert DD/MM/YYYY to YYYY-MM-DD for the input
            function formatDateForInput(dateString) {
              if (!dateString) return '';
              // If already in YYYY-MM-DD format, return as is
              if (/^\d{4}-\d{2}-\d{2}$/.test(dateString)) {
                return dateString;
              }
              // Try to parse as DD/MM/YYYY
              const parts = dateString.split('/');
              if (parts.length === 3) {
                const [day, month, year] = parts;
                return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
              }
              return dateString; // Fallback to original if format is unknown
            }

            // Initialize date pickers when modal is opened
            function initializeDatePickers() {
              // Reinitialize flatpickr on modal open
              if (window.startDatePicker) window.startDatePicker.destroy();
              if (window.endDatePicker) window.endDatePicker.destroy();
              
              window.startDatePicker = flatpickr("#start_date", {
                dateFormat: "d/m/Y",
                allowInput: true,
                onChange: function(selectedDates, dateStr, instance) {
                  if (dateStr) {
                    instance.input.value = dateStr;
                  }
                }
              });
              
              window.endDatePicker = flatpickr("#end_date", {
                dateFormat: "d/m/Y",
                allowInput: true,
                onChange: function(selectedDates, dateStr, instance) {
                  if (dateStr) {
                    instance.input.value = dateStr;
                  }
                }
              });
            }
            
            // Initialize date pickers when modal is opened
            if (createBtn) {
              createBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                openCreateModal();
                initializeDatePickers();
              });
            }

            // Handle form submit: create or update scheduled ad
            if (form) {
              form.addEventListener('submit', async function(e) {
                e.preventDefault();

                const title = titleInput ? titleInput.value.trim() : '';
                // Format dates for display but keep the original value for submission
                const startDate = startDateInput ? formatDateForInput(startDateInput.value) : '';
                const endDate = endDateInput ? formatDateForInput(endDateInput.value) : '';

                if (!title || !startDate || !endDate) {
                  showNotification('Please fill in Title, Start Date, and End Date.', 'error');
                  return;
                }

                if (imageType === 'upload' && !imageData) {
                  showNotification('Please upload an advertisement image.', 'error');
                  return;
                }
                if (imageType === 'url' && !imageUrl) {
                  showNotification('Please provide an image URL.', 'error');
                  return;
                }

                const startTimeVal = (startTimeInput && startTimeInput.value) || '00:00';
                const endTimeVal = (endTimeInput && endTimeInput.value) || '23:59';

                const payload = {
                  title: title,
                  description: descriptionInput ? descriptionInput.value : '',
                  start_date: startDate,
                  end_date: endDate,
                  start_time: startTimeVal + ':00',
                  end_time: endTimeVal + ':00',
                  background_image_type: imageType,
                  background_image: imageType === 'url' ? imageUrl : '',
                  background_image_data: imageType === 'upload' ? imageData : '',
                  is_active: true,
                  created_by: 'admin'
                };

                try {
                  const adIdInput = document.getElementById('adId');
                  const isEditing = adIdInput && adIdInput.value;
                  // Build endpoint with string concatenation to keep Python f-string evaluation out of the URL
                  const endpoint = isEditing ? '/api/scheduled-ads/' + adIdInput.value : '/api/scheduled-ads';
                  const method = isEditing ? 'PUT' : 'POST';

                  const resp = await fetch(endpoint, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                  });

                  const data = await resp.json();
                  if (data.status === 'success') {
                    window.location.reload();
                  } else {
                    showNotification(data.message || 'Failed to save schedule', 'error');
                  }
                } catch (err) {
                  console.error(err);
                  showNotification('Error saving schedule: ' + err.message, 'error');
                }
              });
            }

            // expose closeModal so the Cancel button works
            window.closeModal = closeModal;

            // Function to handle edit ad
            window.editAd = function(adId) {
              // Use simple string concatenation to avoid mixing JS template literals with Python f-strings
              fetch('/api/scheduled-ads/' + adId)
                .then(response => response.json())
                .then(data => {
                  if (data.status === 'success') {
                    const ad = data.data;
                    document.getElementById('modalTitle').textContent = 'Edit Schedule';
                    document.getElementById('adId').value = ad.id;
                    document.getElementById('title').value = ad.title || '';
                    document.getElementById('description').value = ad.description || '';
                    
                    // Format dates for display
                    const startDate = ad.start_date ? formatDateForDisplay(ad.start_date) : '';
                    const endDate = ad.end_date ? formatDateForDisplay(ad.end_date) : '';
                    
                    // Set the values and reinitialize datepickers
                    document.getElementById('start_date').value = startDate;
                    document.getElementById('end_date').value = endDate;
                    
                    // Reinitialize datepickers after setting values
                    initializeDatePickers();
                    document.getElementById('start_time').value = ad.start_time ? ad.start_time.substring(0, 5) : '00:00';
                    document.getElementById('end_time').value = ad.end_time ? ad.end_time.substring(0, 5) : '23:59';
                    
                    // Handle image preview
                    const imagePreview = document.getElementById('adImagePreview');
                    if (ad.background_image_type === 'url' && ad.background_image) {
                      showUrlPanel();
                      document.getElementById('adImageUrl').value = ad.background_image;
                      imageType = 'url';
                      imageUrl = ad.background_image;
                      imagePreview.innerHTML = '<img src="' + ad.background_image + '" alt="Preview" style="max-width: 100%; max-height: 200px;">';
                    } else if (ad.background_image_type === 'upload' && ad.background_image_data) {
                      showUploadPanel();
                      imageType = 'upload';
                      imageData = ad.background_image_data;
                      imagePreview.innerHTML = '<img src="' + ad.background_image_data + '" alt="Preview" style="max-width: 100%; max-height: 200px;">';
                    }
                    
                    openCreateModal();
                  } else {
                    showNotification(data.message || 'Failed to load ad data', 'error');
                  }
                })
                .catch(error => {
                  console.error('Error:', error);
                  showNotification('Error loading ad data: ' + error.message, 'error');
                });
            };

            function openDeleteModal(adId) {
              pendingDeleteId = adId;
              if (deleteModal) {
                deleteModal.classList.add('active');
              }
            }

            function closeDeleteModal() {
              pendingDeleteId = null;
              if (deleteModal) {
                deleteModal.classList.remove('active');
              }
            }

            if (confirmDeleteYes) {
              confirmDeleteYes.addEventListener('click', async function() {
                if (!pendingDeleteId) {
                  closeDeleteModal();
                  return;
                }
                try {
                  // Avoid JS template literals here; keep it simple so the Python f-string doesn't try to interpolate
                  const resp = await fetch('/api/scheduled-ads/' + pendingDeleteId, {
                    method: 'DELETE',
                    headers: { 'Content-Type': 'application/json' },
                  });
                  const data = await resp.json();
                  if (data.status === 'success') {
                    window.location.reload();
                  } else {
                    alert('Error: ' + (data.message || 'Failed to delete schedule'));
                    closeDeleteModal();
                  }
                } catch (error) {
                  console.error('Error:', error);
                  alert('Error deleting schedule: ' + error.message);
                  closeDeleteModal();
                }
              });
            }

            if (confirmDeleteNo) {
              confirmDeleteNo.addEventListener('click', function() {
                closeDeleteModal();
              });
            }

            // Function to handle delete ad (trigger modal)
            window.deleteAd = function(adId) {
              openDeleteModal(adId);
            };
          });
        </script>
      </body>
    </html>
    """
    return HTMLResponse(content=html)

# ==== Admin Panel for Page Settings ====
@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    if not request.session.get("logged_in"):
        return RedirectResponse("/dashboard")
    
    settings = get_page_settings()
    bg_type = settings.get('background_image_type', 'url')
    bg_url_value = settings.get('background_image', 'url(../img/nuanu.png)')
    bg_data_value = settings.get('background_image_data', '')
    bg_data_attr = bg_data_value.replace('"', '&quot;') if bg_data_value else ""
    bg_url_attr = bg_url_value.replace('"', '&quot;') if bg_url_value else ""
    google_ready = "true" if GOOGLE_OAUTH_ENABLED else "false"
    
    html = f"""
    <html>
      <head>
        <title>Admin Panel - Page Settings</title>
        <style>
          body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea, #764ba2);
            padding: 20px;
            margin: 0;
          }}
          .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
          }}
          h1 {{
            color: #333;
            margin-bottom: 10px;
          }}
          .subtitle {{
            color: #666;
            margin-bottom: 30px;
          }}
          .section {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
          }}
          .section h2 {{
            color: #667eea;
            margin-top: 0;
            font-size: 18px;
          }}
          .form-group {{
            margin-bottom: 20px;
          }}
          .form-group label {{
            display: block;
            font-weight: 600;
            margin-bottom: 8px;
            color: #333;
          }}
          .radio-group {{
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            margin-bottom: 14px;
          }}
          .radio-option {{
            position: relative;
            display: inline-flex;
            align-items: center;
            gap: 10px;
            padding: 12px 18px;
            border-radius: 10px;
            border: 2px solid #e1e8ed;
            background: white;
            cursor: pointer;
            transition: all 0.2s ease;
            font-weight: 600;
            color: #4a5568;
          }}
          .radio-option input {{
            position: absolute;
            opacity: 0;
            pointer-events: none;
          }}
          .radio-option.active {{
            border-color: #667eea;
            background: #eef2ff;
            color: #4338ca;
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.15);
          }}
          .hidden {{
            display: none !important;
          }}
          .background-actions {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 12px;
          }}
          .background-actions button {{
            flex: 1;
            min-width: 160px;
          }}
          .background-info {{
            font-size: 12px;
            color: #666;
            margin-top: 6px;
          }}
          .background-preview {{
            margin-top: 16px;
            border-radius: 12px;
            border: 1px solid #e1e8ed;
            height: 150px;
            background: #f1f5f9;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #94a3b8;
            font-size: 14px;
            position: relative;
            overflow: hidden;
          }}
          .background-preview img {{
            max-width: 100%;
            max-height: 100%;
            object-fit: cover;
          }}
          .background-preview .preview-badge {{
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(15, 23, 42, 0.7);
            color: white;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 600;
          }}
          .oauth-status {{
            font-size: 12px;
            color: #6b7280;
            margin-top: 6px;
          }}
          .toggle-switch {{
            position: relative;
            display: inline-block;
            width: 60px;
            height: 34px;
          }}
          .toggle-switch input {{
            opacity: 0;
            width: 0;
            height: 0;
          }}
          .slider {{
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #ccc;
            transition: .4s;
            border-radius: 34px;
          }}
          .slider:before {{
            position: absolute;
            content: "";
            height: 26px;
            width: 26px;
            left: 4px;
            bottom: 4px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
          }}
          input:checked + .slider {{
            background-color: #667eea;
          }}
          input:checked + .slider:before {{
            transform: translateX(26px);
          }}
          input[type="text"], input[type="color"], textarea {{
            width: 100%;
            padding: 12px;
            border: 2px solid #e1e8ed;
            border-radius: 8px;
            font-size: 14px;
            box-sizing: border-box;
          }}
          textarea {{
            min-height: 80px;
            resize: vertical;
          }}
          .button-group {{
            display: flex;
            gap: 10px;
            margin-top: 30px;
          }}
          button {{
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: all 0.3s;
          }}
          button:hover {{
            background: #5a67d8;
            transform: translateY(-2px);
          }}
          .btn-secondary {{
            background: #6c757d;
          }}
          .btn-secondary:hover {{
            background: #5a6268;
          }}
          .preview-link {{
            display: inline-block;
            margin-left: 10px;
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
          }}
          .preview-link:hover {{
            text-decoration: underline;
          }}
          .success-message {{
            background: #d4edda;
            color: #155724;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: none;
          }}
          /* Loading Overlay */
          .loading-overlay {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.7);
            z-index: 9999;
            justify-content: center;
            align-items: center;
          }}
          .loading-overlay.active {{
            display: flex;
          }}
          .loading-content {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            text-align: center;
          }}
          .spinner {{
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
          }}
          @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
          }}
          /* Success Popup */
          .success-popup {{
            display: none;
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) scale(0.7);
            background: white;
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            z-index: 10000;
            text-align: center;
            opacity: 0;
            transition: all 0.3s ease;
          }}
          .success-popup.active {{
            display: block;
            opacity: 1;
            transform: translate(-50%, -50%) scale(1);
          }}
          .success-icon {{
            width: 80px;
            height: 80px;
            border-radius: 50%;
            background: #10b981;
            margin: 0 auto 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: scaleIn 0.5s ease;
          }}
          @keyframes scaleIn {{
            0% {{ transform: scale(0); }}
            50% {{ transform: scale(1.1); }}
            100% {{ transform: scale(1); }}
          }}
          .success-icon::after {{
            content: '✓';
            color: white;
            font-size: 50px;
            font-weight: bold;
          }}
          .success-popup h2 {{
            color: #10b981;
            margin: 0 0 10px 0;
          }}
          .success-popup p {{
            color: #666;
            margin: 0;
          }}
          .nav-links {{
            margin-bottom: 20px;
          }}
          .nav-links a {{
            color: #667eea;
            text-decoration: none;
            margin-right: 15px;
            font-weight: 600;
          }}
          .nav-links a:hover {{
            text-decoration: underline;
          }}
        </style>
      </head>
      <body>
        <!-- Loading Overlay -->
        <div class="loading-overlay" id="loading-overlay">
          <div class="loading-content">
            <div class="spinner"></div>
            <p style="color: #333; font-weight: 600;">Saving settings...</p>
          </div>
        </div>
        
        <!-- Success Popup -->
        <div class="success-popup" id="success-popup">
          <div class="success-icon"></div>
          <h2>Success!</h2>
          <p>Your settings have been saved successfully</p>
        </div>
        
        <div class="container">
          <div class="nav-links">
            <a href="/dashboard">← Back to Dashboard</a>
            <a href="/admin/scheduler">📅 CMS Scheduler</a>
            <a href="/login" target="_blank">Preview Login Page →</a>
          </div>
          
          <h1>⚙️ Admin Panel</h1>
          <p class="subtitle">Manage your login page settings and features</p>
          
          <div id="success-message" class="success-message">
            ✓ Settings saved successfully!
          </div>
          
          <form id="settings-form">
            <!-- Login Features Section -->
            <div class="section">
              <h2>🔐 Login Features</h2>
              
              <div class="form-group">
                <label>
                  Google Login Button
                  <label class="toggle-switch">
                    <input type="checkbox" id="google_login_enabled" 
                           {"checked" if settings.get('google_login_enabled') == 'true' else ""}>
                    <span class="slider"></span>
                  </label>
                </label>
                <div class="oauth-status">
                  {"✅ Google OAuth credentials detected." if GOOGLE_OAUTH_ENABLED else "⚠️ Google OAuth credentials are missing. The Google button will appear but stay offline until credentials are added to the server."}
                </div>
              </div>
              
              <div class="form-group">
                <label>
                  Facebook Login Button
                  <label class="toggle-switch">
                    <input type="checkbox" id="facebook_login_enabled"
                           {"checked" if settings.get('facebook_login_enabled') == 'true' else ""}>
                    <span class="slider"></span>
                  </label>
                </label>
                <div class="oauth-status">
                  {"✅ Facebook OAuth credentials detected." if FACEBOOK_OAUTH_ENABLED else "⚠️ Facebook OAuth credentials are missing. The Facebook button will appear but stay offline until credentials are added to the server."}
                </div>
              </div>
            </div>
            
            <!-- OAuth Credentials Section -->
            <div class="section">
              <h2>🔑 OAuth Credentials</h2>
              <p style="color: #666; font-size: 14px; margin-bottom: 20px;">
                Configure your Google and Facebook OAuth credentials. Changes will be saved to the .env file and take effect immediately.
              </p>
              
              <div class="form-group">
                <label for="google_client_id">Google Client ID</label>
                <input type="text" id="google_client_id" 
                       value="{GOOGLE_CLIENT_ID or ''}"
                       placeholder="Enter your Google OAuth Client ID">
                <small style="color: #666; display: block; margin-top: 5px;">
                  Get this from <a href="https://console.cloud.google.com/apis/credentials" target="_blank">Google Cloud Console</a>
                </small>
              </div>
              
              <div class="form-group">
                <label for="google_client_secret">Google Client Secret</label>
                <input type="password" id="google_client_secret" 
                       value="{GOOGLE_CLIENT_SECRET or ''}"
                       placeholder="Enter your Google OAuth Client Secret">
                <small style="color: #666; display: block; margin-top: 5px;">
                  Keep this secret secure. It will be stored in the .env file.
                </small>
              </div>
              
              <div class="form-group">
                <label for="facebook_client_id">Facebook App ID</label>
                <input type="text" id="facebook_client_id" 
                       value="{FACEBOOK_CLIENT_ID or ''}"
                       placeholder="Enter your Facebook App ID">
                <small style="color: #666; display: block; margin-top: 5px;">
                  Get this from <a href="https://developers.facebook.com/apps/" target="_blank">Facebook Developers</a>
                </small>
              </div>
              
              <div class="form-group">
                <label for="facebook_client_secret">Facebook App Secret</label>
                <input type="password" id="facebook_client_secret" 
                       value="{FACEBOOK_CLIENT_SECRET or ''}"
                       placeholder="Enter your Facebook App Secret">
                <small style="color: #666; display: block; margin-top: 5px;">
                  Keep this secret secure. It will be stored in the .env file.
                </small>
              </div>
            </div>
            
            <!-- Page Appearance Section -->
            <div class="section">
              <h2>🎨 Page Appearance</h2>
              
              <div class="form-group">
                <label for="page_title">Page Title</label>
                <input type="text" id="page_title" 
                       value="{settings.get('page_title', 'Welcome To NUANU Free WiFi')}">
              </div>
              
              <div class="form-group">
                <label for="button_text">Button Text</label>
                <input type="text" id="button_text" 
                       value="{settings.get('button_text', 'Connect to WiFi')}">
              </div>
              
              <div class="form-group">
                <label>Background Image</label>
                <p class="helper-text" style="margin-top: -5px;">Upload from your computer.</p>
                
                <div id="background-upload-fields">
                  <input type="file" id="background_file" accept="image/*" style="display: none;">
                  <div class="background-actions">
                    <button type="button" id="choose-file-btn">📁 Choose Image</button>
                    <button type="button" class="btn-secondary" id="clear-upload-btn">Remove</button>
                  </div>
                  <div class="background-info">
                    Supported formats: JPG or PNG up to 3 MB.
                  </div>
                </div>
                
                <div class="background-preview" id="background-preview">
                  <span id="background-preview-label">No image selected</span>
                </div>
                <input type="hidden" id="background_image_data" value="{bg_data_attr}">
                <input type="hidden" id="background_image" value="">
                <input type="hidden" id="background_color" value="{settings.get('background_color', '#667eea')}">
              </div>
            </div>
            
            <div class="button-group">
              <button type="submit">💾 Save Settings</button>
              <button type="button" class="btn-secondary" onclick="window.location.href='/dashboard'">
                Cancel
              </button>
            </div>
          </form>
        </div>
        
        <script>
          // Wait for DOM to be ready
          document.addEventListener('DOMContentLoaded', function() {{
            console.log('DOM loaded, initializing file upload...');
            
            // File upload variables
            const MAX_UPLOAD_SIZE = 3 * 1024 * 1024; // 3 MB
            const backgroundImageDataInput = document.getElementById('background_image_data');
            const backgroundPreview = document.getElementById('background-preview');
            const chooseFileBtn = document.getElementById('choose-file-btn');
            const clearUploadBtn = document.getElementById('clear-upload-btn');
            const backgroundFileInput = document.getElementById('background_file');
            const previewBadgeClass = 'preview-badge';
            
            console.log('Elements found:', {{
              chooseFileBtn: !!chooseFileBtn,
              backgroundFileInput: !!backgroundFileInput,
              clearUploadBtn: !!clearUploadBtn,
              backgroundPreview: !!backgroundPreview,
              backgroundImageDataInput: !!backgroundImageDataInput
            }});
            
            // Render preview function
            function renderPreview() {{
              if (!backgroundPreview || !backgroundImageDataInput) return;
              backgroundPreview.style.backgroundImage = 'none';
              backgroundPreview.innerHTML = '';
              
              const data = backgroundImageDataInput.value.trim();
              if (data) {{
                const img = document.createElement('img');
                img.src = data;
                backgroundPreview.appendChild(img);
                const badge = document.createElement('span');
                badge.className = previewBadgeClass;
                badge.textContent = 'Uploaded';
                backgroundPreview.appendChild(badge);
              }} else {{
                backgroundPreview.textContent = 'Upload an image to preview';
              }}
            }}
            
            // Choose Image button - FIXED!
            if (chooseFileBtn) {{
              chooseFileBtn.addEventListener('click', function(e) {{
                e.preventDefault();
                e.stopPropagation();
                console.log('Choose Image button clicked!');
                if (backgroundFileInput) {{
                  console.log('Triggering file input click...');
                  backgroundFileInput.click();
                }} else {{
                  console.error('backgroundFileInput not found!');
                  alert('File input not found. Please refresh the page.');
                }}
              }});
              console.log('Choose Image button event listener attached');
            }} else {{
              console.error('Choose Image button not found!');
            }}
            
            // Clear/Remove button
            if (clearUploadBtn) {{
              clearUploadBtn.addEventListener('click', function() {{
                if (backgroundFileInput) backgroundFileInput.value = '';
                if (backgroundImageDataInput) backgroundImageDataInput.value = '';
                renderPreview();
              }});
            }}
            
            // File input change handler
            if (backgroundFileInput) {{
              backgroundFileInput.addEventListener('change', function(event) {{
                const file = event.target.files[0];
                if (!file) return;
                
                if (!file.type.startsWith('image/')) {{
                  alert('Please choose an image file.');
                  event.target.value = '';
                  return;
                }}
                if (file.size > MAX_UPLOAD_SIZE) {{
                  alert('Image is too large. Choose a file smaller than 3 MB.');
                  event.target.value = '';
                  return;
                }}
                
                const reader = new FileReader();
                reader.onload = function(e) {{
                  if (backgroundImageDataInput) {{
                    backgroundImageDataInput.value = e.target.result;
                    renderPreview();
                  }}
                }};
                reader.onerror = function() {{
                  alert('Failed to read the image file.');
                }};
                reader.readAsDataURL(file);
              }});
            }}
            
            // Initialize preview on page load
            renderPreview();
            
            // Form submit handler
            const loadingOverlay = document.getElementById('loading-overlay');
            const settingsForm = document.getElementById('settings-form');
            if (settingsForm) {{
              settingsForm.addEventListener('submit', async (e) => {{
              e.preventDefault();
              
              if (!backgroundImageDataInput.value) {{
                alert('Please upload an image first.');
                return;
              }}
              
              loadingOverlay.classList.add('active');
              
              const settings = {{
                google_login_enabled: document.getElementById('google_login_enabled').checked ? 'true' : 'false',
                facebook_login_enabled: document.getElementById('facebook_login_enabled').checked ? 'true' : 'false',
                background_image: '',
                background_image_type: 'upload',
                background_image_data: backgroundImageDataInput.value,
                background_color: document.getElementById('background_color').value,
                page_title: document.getElementById('page_title').value,
                button_text: document.getElementById('button_text').value
              }};
              
              // Get OAuth credentials
              const oauthCredentials = {{
                google_client_id: document.getElementById('google_client_id').value.trim(),
                google_client_secret: document.getElementById('google_client_secret').value.trim(),
                facebook_client_id: document.getElementById('facebook_client_id').value.trim(),
                facebook_client_secret: document.getElementById('facebook_client_secret').value.trim()
              }};
              
              try {{
                // Save page settings
                const settingsResponse = await fetch('/api/settings', {{
                  method: 'POST',
                  headers: {{ 'Content-Type': 'application/json' }},
                  body: JSON.stringify(settings)
                }});
                
                // Save OAuth credentials
                const credentialsResponse = await fetch('/api/oauth-credentials', {{
                  method: 'POST',
                  headers: {{ 'Content-Type': 'application/json' }},
                  body: JSON.stringify(oauthCredentials)
                }});
                
                // Wait for both responses
                const [settingsData, credentialsData] = await Promise.all([
                  settingsResponse.json().catch(() => ({{}})),
                  credentialsResponse.json().catch(() => ({{}}))
                ]);
                
                setTimeout(() => {{
                  loadingOverlay.classList.remove('active');
                  
                  let settingsOk = settingsResponse.ok;
                  let credentialsOk = credentialsResponse.ok;
                  
                  if (settingsOk && credentialsOk) {{
                    const successPopup = document.getElementById('success-popup');
                    successPopup.classList.add('active');
                    setTimeout(() => {{
                      successPopup.classList.remove('active');
                      // Reload page after 2 seconds to show updated OAuth status
                      setTimeout(() => {{
                        window.location.reload();
                      }}, 500);
                    }}, 2000);
                  }} else {{
                    let errorMsg = 'Failed to save settings.';
                    if (!settingsOk) {{
                      errorMsg = 'Settings: ' + (settingsData.message || settingsResponse.statusText);
                    }}
                    if (!credentialsOk) {{
                      errorMsg += '\\nCredentials: ' + (credentialsData.message || credentialsResponse.statusText);
                    }}
                    alert(errorMsg);
                  }}
                }}, 800);
              }} catch (error) {{
                loadingOverlay.classList.remove('active');
                alert('Error saving settings: ' + error.message);
              }}
              }});
            }}
          }});
        </script>
      </body>
    </html>
    """
    return HTMLResponse(content=html)

# ==== API Endpoint to Update Settings ====
@app.post("/api/settings")
async def update_settings(request: Request):
    if not request.session.get("logged_in"):
        return JSONResponse({"status": "error", "message": "Unauthorized"}, status_code=401)
    
    data = await request.json()
    img_mode = data.get("background_image_type")
    data_url = (data.get("background_image_data") or "").strip()
    
    if img_mode == "upload":
        if not data_url:
            return JSONResponse({"status": "error", "message": "Please upload an image before saving."}, status_code=400)
        if not data_url.startswith("data:image/"):
            return JSONResponse({"status": "error", "message": "Invalid image format."}, status_code=400)
        if len(data_url) > 8_000_000:  # ~6 MB when decoded
            return JSONResponse({"status": "error", "message": "Image is too large. Please keep it under 6 MB."}, status_code=400)
    else:
        data["background_image_data"] = ""
    
    if img_mode == "none":
        data["background_image"] = ""
    
    for key, value in data.items():
        update_page_setting(key, value)
    
    return JSONResponse({"status": "success", "message": "Settings updated"})

# ==== API Endpoint to Get Settings (for dynamic login page) ====
@app.get("/api/settings")
async def get_settings():
    settings = get_page_settings()
    settings["google_oauth_available"] = "true" if GOOGLE_OAUTH_ENABLED else "false"
    settings["facebook_oauth_available"] = "true" if FACEBOOK_OAUTH_ENABLED else "false"
    return JSONResponse(settings)

# ==== API Endpoint to Update OAuth Credentials ====
@app.post("/api/oauth-credentials")
async def update_oauth_credentials(request: Request):
    if not request.session.get("logged_in"):
        return JSONResponse({"status": "error", "message": "Unauthorized"}, status_code=401)
    
    data = await request.json()
    
    # Prepare updates for .env file
    updates = {}
    if "google_client_id" in data:
        updates["GOOGLE_CLIENT_ID"] = data["google_client_id"]
    if "google_client_secret" in data:
        updates["GOOGLE_CLIENT_SECRET"] = data["google_client_secret"]
    if "facebook_client_id" in data:
        updates["FACEBOOK_CLIENT_ID"] = data["facebook_client_id"]
    if "facebook_client_secret" in data:
        updates["FACEBOOK_CLIENT_SECRET"] = data["facebook_client_secret"]
    
    # Update .env file
    try:
        update_env_file(updates)
        
        # Reload OAuth configuration
        reload_oauth_config()
        
        return JSONResponse({
            "status": "success", 
            "message": "OAuth credentials updated successfully. OAuth configuration has been reloaded."
        })
    except Exception as e:
        return JSONResponse({
            "status": "error", 
            "message": f"Failed to update credentials: {str(e)}"
        }, status_code=500)

# ==== CMS Scheduler API Endpoints ====
@app.get("/api/scheduled-ads")
async def get_scheduled_ads_api(request: Request):
    """Get all scheduled ads for admin panel"""
    if not request.session.get("logged_in"):
        return JSONResponse({"status": "error", "message": "Unauthorized"}, status_code=401)
    ads = get_all_scheduled_ads()
    return JSONResponse({"status": "success", "ads": ads})

@app.get("/api/scheduled-ads/{ad_id}")
async def get_scheduled_ad_api(request: Request, ad_id: int):
    """Get a specific scheduled ad"""
    if not request.session.get("logged_in"):
        return JSONResponse({"status": "error", "message": "Unauthorized"}, status_code=401)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, title, description, background_image, background_image_type,
               background_image_data, background_color, page_title, button_text,
               start_date, end_date, start_time, end_time, is_active, created_by
        FROM scheduled_ads
        WHERE id = %s
    """, (ad_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    if not row:
        return JSONResponse({"status": "error", "message": "Ad not found"}, status_code=404)

    # Shape payload so scheduler JS can use data.data while keeping backward compatibility
    ad_payload = {
        'id': row[0],
        'title': row[1],
        'description': row[2],
        'background_image': row[3],
        'background_image_type': row[4],
        'background_image_data': row[5],
        'background_color': row[6],
        'page_title': row[7],
        'button_text': row[8],
        'start_date': str(row[9]),
        'end_date': str(row[10]),
        'start_time': str(row[11]),
        'end_time': str(row[12]),
        'is_active': row[13],
        'created_by': row[14],
    }

    return JSONResponse({
        "status": "success",
        "data": ad_payload,
        "ad": ad_payload,
    })

@app.post("/api/scheduled-ads")
async def create_scheduled_ad(request: Request):
    """Create a new scheduled ad"""
    if not request.session.get("logged_in"):
        return JSONResponse({"status": "error", "message": "Unauthorized"}, status_code=401)
    
    data = await request.json()
    
    # Validate required fields
    required_fields = ['title', 'start_date', 'end_date']
    for field in required_fields:
        if field not in data or not data[field]:
            return JSONResponse({"status": "error", "message": f"Missing required field: {field}"}, status_code=400)
    
    # Parse dates and times
    try:
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        start_time = data.get('start_time', '00:00:00')
        end_time = data.get('end_time', '23:59:59')
        
        # Check for overlapping schedules
        conn = get_connection()
        cur = conn.cursor()
        
        # Query to find any active schedules that overlap with the new schedule
        overlap_query = """
            SELECT id, title, start_date, end_date, start_time, end_time
            FROM scheduled_ads
            WHERE is_active = TRUE
              AND (
                -- Case 1: New schedule starts during an existing schedule
                (start_date <= %s AND end_date >= %s AND 
                 (start_date < %s OR (start_date = %s AND start_time <= %s)) AND
                 (end_date > %s OR (end_date = %s AND end_time >= %s)))
                OR
                -- Case 2: New schedule ends during an existing schedule
                (start_date <= %s AND end_date >= %s AND
                 (start_date < %s OR (start_date = %s AND start_time <= %s)) AND
                 (end_date > %s OR (end_date = %s AND end_time >= %s)))
                OR
                -- Case 3: New schedule completely contains an existing schedule
                (start_date >= %s AND end_date <= %s AND
                 (start_date > %s OR (start_date = %s AND start_time >= %s)) AND
                 (end_date < %s OR (end_date = %s AND end_time <= %s)))
                OR
                -- Case 4: Existing schedule completely contains the new schedule
                (start_date <= %s AND end_date >= %s AND
                 (start_date < %s OR (start_date = %s AND start_time <= %s)) AND
                 (end_date > %s OR (end_date = %s AND end_time >= %s)))
              )
        """
        
        params = (
            # Case 1: New schedule starts during existing
            start_date, start_date,
            start_date, start_date, start_time,
            start_date, start_date, start_time,
            # Case 2: New schedule ends during existing
            end_date, end_date,
            end_date, end_date, end_time,
            end_date, end_date, end_time,
            # Case 3: New schedule contains existing
            start_date, end_date,
            start_date, start_date, start_time,
            end_date, end_date, end_time,
            # Case 4: Existing contains new schedule
            start_date, end_date,
            start_date, start_date, start_time,
            end_date, end_date, end_time,
        )
        
        cur.execute(overlap_query, params)
        overlapping = cur.fetchone()
        
        if overlapping:
            cur.close()
            conn.close()
            overlap_title = overlapping[1]
            overlap_dates = f"{overlapping[2]} to {overlapping[3]}"
            return JSONResponse({
                "status": "error", 
                "message": f"A schedule already exists for this date/time range: '{overlap_title}' ({overlap_dates}). Please choose a different time period."
            }, status_code=400)
        
        # No overlap found, proceed with creation
        cur.execute("""
            INSERT INTO scheduled_ads (
                title, description, background_image, background_image_type,
                background_image_data, background_color, page_title, button_text,
                start_date, end_date, start_time, end_time, is_active, created_by
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data.get('title'),
            data.get('description'),
            data.get('background_image'),
            data.get('background_image_type', 'url'),
            data.get('background_image_data', ''),
            data.get('background_color', '#667eea'),
            data.get('page_title'),
            data.get('button_text'),
            start_date,
            end_date,
            start_time,
            end_time,
            data.get('is_active', True),
            data.get('created_by', 'admin')
        ))
        
        ad_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        return JSONResponse({"status": "success", "message": "Scheduled ad created", "id": ad_id})
    
    except Exception as e:
        if 'conn' in locals() and conn:
            conn.rollback()
            if 'cur' in locals() and cur:
                cur.close()
            conn.close()
        return JSONResponse({"status": "error", "message": f"Error creating schedule: {str(e)}"}, status_code=500)


@app.put("/api/scheduled-ads/{ad_id}")
async def update_scheduled_ad(request: Request, ad_id: int):
    """Update a scheduled ad"""
    if not request.session.get("logged_in"):
        return JSONResponse({"status": "error", "message": "Unauthorized"}, status_code=401)
    
    data = await request.json()
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # If dates/times are being updated, check for overlaps (excluding current schedule)
        if any(key in data for key in ['start_date', 'end_date', 'start_time', 'end_time']):
            # First, get the current schedule's dates/times
            cur.execute("""
                SELECT start_date, end_date, start_time, end_time
                FROM scheduled_ads
                WHERE id = %s
            """, (ad_id,))
            current = cur.fetchone()
            
            if not current:
                cur.close()
                conn.close()
                return JSONResponse({"status": "error", "message": "Ad not found"}, status_code=404)
            
            # Use new values if provided, otherwise use current values
            start_date = data.get('start_date') or current[0]
            end_date = data.get('end_date') or current[1]
            start_time = data.get('start_time') or current[2]
            end_time = data.get('end_time') or current[3]
            
            # Check for overlapping schedules (excluding the current one being edited)
            overlap_query = """
                SELECT id, title, start_date, end_date, start_time, end_time
                FROM scheduled_ads
                WHERE is_active = TRUE
                  AND id != %s
                  AND (
                    -- Case 1: New schedule starts during an existing schedule
                    (start_date <= %s AND end_date >= %s AND 
                     (start_date < %s OR (start_date = %s AND start_time <= %s)) AND
                     (end_date > %s OR (end_date = %s AND end_time >= %s)))
                    OR
                    -- Case 2: New schedule ends during an existing schedule
                    (start_date <= %s AND end_date >= %s AND
                     (start_date < %s OR (start_date = %s AND start_time <= %s)) AND
                     (end_date > %s OR (end_date = %s AND end_time >= %s)))
                    OR
                    -- Case 3: New schedule completely contains an existing schedule
                    (start_date >= %s AND end_date <= %s AND
                     (start_date > %s OR (start_date = %s AND start_time >= %s)) AND
                     (end_date < %s OR (end_date = %s AND end_time <= %s)))
                    OR
                    -- Case 4: Existing schedule completely contains the new schedule
                    (start_date <= %s AND end_date >= %s AND
                     (start_date < %s OR (start_date = %s AND start_time <= %s)) AND
                     (end_date > %s OR (end_date = %s AND end_time >= %s)))
                  )
            """
            
            params = (
                ad_id,  # Exclude current schedule
                # Case 1: New schedule starts during existing
                start_date, start_date,
                start_date, start_date, start_time,
                start_date, start_date, start_time,
                # Case 2: New schedule ends during existing
                end_date, end_date,
                end_date, end_date, end_time,
                end_date, end_date, end_time,
                # Case 3: New schedule contains existing
                start_date, end_date,
                start_date, start_date, start_time,
                end_date, end_date, end_time,
                # Case 4: Existing contains new schedule
                start_date, end_date,
                start_date, start_date, start_time,
                end_date, end_date, end_time,
            )
            
            cur.execute(overlap_query, params)
            overlapping = cur.fetchone()
            
            if overlapping:
                cur.close()
                conn.close()
                overlap_title = overlapping[1]
                overlap_dates = f"{overlapping[2]} to {overlapping[3]}"
                return JSONResponse({
                    "status": "error", 
                    "message": f"A schedule already exists for this date/time range: '{overlap_title}' ({overlap_dates}). Please choose a different time period."
                }, status_code=400)
        
        # No overlap found, proceed with update
        cur.execute("""
            UPDATE scheduled_ads SET
                title = COALESCE(%s, title),
                description = COALESCE(%s, description),
                background_image = COALESCE(%s, background_image),
                background_image_type = COALESCE(%s, background_image_type),
                background_image_data = COALESCE(%s, background_image_data),
                background_color = COALESCE(%s, background_color),
                page_title = COALESCE(%s, page_title),
                button_text = COALESCE(%s, button_text),
                start_date = COALESCE(%s, start_date),
                end_date = COALESCE(%s, end_date),
                start_time = COALESCE(%s, start_time),
                end_time = COALESCE(%s, end_time),
                is_active = COALESCE(%s, is_active),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id
        """, (
            data.get('title'),
            data.get('description'),
            data.get('background_image'),
            data.get('background_image_type'),
            data.get('background_image_data'),
            data.get('background_color'),
            data.get('page_title'),
            data.get('button_text'),
            data.get('start_date'),
            data.get('end_date'),
            data.get('start_time'),
            data.get('end_time'),
            data.get('is_active'),
            ad_id
        ))
        
        if not cur.fetchone():
            cur.close()
            conn.close()
            return JSONResponse({"status": "error", "message": "Ad not found"}, status_code=404)
        
        conn.commit()
        cur.close()
        conn.close()
        
        return JSONResponse({"status": "success", "message": "Scheduled ad updated"})
    
    except Exception as e:
        if 'conn' in locals() and conn:
            conn.rollback()
            if 'cur' in locals() and cur:
                cur.close()
            conn.close()
        return JSONResponse({"status": "error", "message": f"Error updating schedule: {str(e)}"}, status_code=500)


@app.delete("/api/scheduled-ads/{ad_id}")
async def delete_scheduled_ad(request: Request, ad_id: int):
    """Delete a scheduled ad"""
    if not request.session.get("logged_in"):
        return JSONResponse({"status": "error", "message": "Unauthorized"}, status_code=401)
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM scheduled_ads WHERE id = %s RETURNING id", (ad_id,))
    
    if not cur.fetchone():
        cur.close()
        conn.close()
        return JSONResponse({"status": "error", "message": "Ad not found"}, status_code=404)
    
    conn.commit()
    cur.close()
    conn.close()
    
    return JSONResponse({"status": "success", "message": "Scheduled ad deleted"})

@app.get("/api/active-ad")
async def get_active_ad_public():
    """Public endpoint for the login page to fetch the current scheduled advertisement."""
    ad = get_active_scheduled_ad()
    if not ad:
        return JSONResponse({"status": "success", "ad": None})
    
    image_src = build_ad_image_src(
        ad.get('background_image'),
        ad.get('background_image_type'),
        ad.get('background_image_data')
    )
    
    if not image_src:
        # Without an image there's nothing to display as an advertisement, so return None.
        return JSONResponse({"status": "success", "ad": None})
    
    payload = {
        "id": ad.get('id'),
        "title": ad.get('title'),
        "description": ad.get('description'),
        "start_date": serialize_time_value(ad.get('start_date')),
        "end_date": serialize_time_value(ad.get('end_date')),
        "start_time": serialize_time_value(ad.get('start_time')),
        "end_time": serialize_time_value(ad.get('end_time')),
        "image": image_src
    }
    return JSONResponse({"status": "success", "ad": payload})

# ==== Dynamic Login Page ====
def get_safe_settings():
    """Get page settings with proper error handling"""
    default_settings = {
        'background_image': 'url(../img/nuanu.png)',
        'background_image_type': 'url',
        'background_image_data': '',
        'background_color': '#667eea',
        'page_title': 'Welcome To NUANU Free WiFi',
        'button_text': 'Connect to WiFi',
        'google_login_enabled': 'false',
        'facebook_login_enabled': 'false'
    }
    
    try:
        settings = get_page_settings()
        # Ensure all required settings exist
        for key in default_settings:
            if key not in settings:
                settings[key] = default_settings[key]
        return settings
    except Exception as e:
        print(f"Error getting page settings: {e}")
        return default_settings

def get_safe_ad_content():
    """Generate ad section HTML for all active scheduled ads with safe fallbacks."""
    try:
        conn = None
        cur = None
        rows = []

        try:
            conn = get_connection()
            cur = conn.cursor()

            now = datetime.now()
            current_date = now.date()
            current_time = now.time()

            query = """
                SELECT id, title, description, background_image, background_image_type,
                       background_image_data, background_color, page_title, button_text,
                       start_date, end_date, start_time, end_time, is_active, created_by
                FROM scheduled_ads
                WHERE is_active = TRUE
                  AND start_date <= %s
                  AND end_date >= %s
                  AND (
                    (start_date < %s AND end_date > %s) OR
                    (start_date = %s AND start_time <= %s AND end_date > %s) OR
                    (start_date < %s AND end_date = %s AND end_time >= %s) OR
                    (start_date = %s AND end_date = %s AND start_time <= %s AND end_time >= %s)
                  )
                ORDER BY start_date DESC, start_time DESC
            """

            params = (
                current_date, current_date,
                current_date, current_date,
                current_date, current_time, current_date,
                current_date, current_date, current_time,
                current_date, current_date, current_time, current_time,
            )

            cur.execute(query, params)
            rows = cur.fetchall()
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

        if not rows:
            return """
            <div class="card ad-card">
              <div class="ad-image-wrapper">
                <img src="/img/nuanu.png" alt="NUANU WiFi">
                <div class="ad-label">Welcome</div>
              </div>
              <div class="ad-content">
                <h2>Welcome to NUANU WiFi</h2>
                <p class="ad-description">Please connect to our WiFi network</p>
              </div>
            </div>
            """

        cards_html: list[str] = []

        for row in rows:
            background_image = row[3]
            background_image_type = row[4]
            background_image_data = row[5]

            ad_image_src = build_ad_image_src(
                background_image,
                background_image_type,
                background_image_data,
            )

            if not ad_image_src:
                ad_image_src = "/img/nuanu.png"

            end_date_str = serialize_time_value(row[10])
            end_time_str = serialize_time_value(row[12])
            timeframe = (
                f"Active until {end_date_str} {end_time_str}".strip()
                if (end_date_str or end_time_str)
                else ""
            )

            title = html.escape(row[1] or "Latest Promotion")
            description = html.escape(row[2] or "").replace("\n", "<br>")

            card_html = f"""
        <div class="card ad-card">
          <div class="ad-image-wrapper">
            <img src="{html.escape(ad_image_src, quote=True)}" alt="Advertisement for {title}">
            <div class="ad-label">Featured Offer</div>
          </div>
          <div class="ad-content">
            {f'<p class="ad-timeframe">{timeframe}</p>' if timeframe else ''}
            <h2>{title}</h2>
            <p class="ad-description">{description or 'Stay tuned for more news from NUANU.'}</p>
          </div>
        </div>
            """
            cards_html.append(card_html)

        return "\n".join(cards_html)

    except Exception as e:
        print(f"Error generating ad content: {e}")
        return """
        <div class="card ad-card">
          <div class="ad-content">
            <h2>Welcome</h2>
            <p class="ad-description">Welcome to our WiFi network</p>
          </div>
        </div>
        """

@app.get("/login", response_class=HTMLResponse)
@app.post("/login")
async def dynamic_login(request: Request):
    # Handle POST request (form submission)
    if request.method == "POST":
        try:
            form_data = await request.form()
            email = form_data.get("email", "").strip()
            # Here you can add your email processing logic
            # For now, we'll just redirect back to the login page
            return RedirectResponse(url="/login", status_code=303)
        except Exception as e:
            print(f"Error processing form: {e}")
            # On error, still redirect to login but could show error message
            return RedirectResponse(url="/login", status_code=303)
    
    # Handle GET request (page load)
    try:
        # Get safe settings with defaults
        settings = get_safe_settings()
        
        # Set default values with fallbacks
        bg_image_raw = settings.get('background_image', '')
        bg_image_type = settings.get('background_image_type', 'url')
        bg_image_data = settings.get('background_image_data', '')
        bg_color = settings.get('background_color', '#667eea')
        page_title = settings.get('page_title', 'Welcome To NUANU Free WiFi')
        button_text = settings.get('button_text', 'Connect to WiFi')
        
        # Get ad content safely
        ad_section_html = get_safe_ad_content()
        
        # Set up OAuth buttons
        google_toggle_enabled = settings.get('google_login_enabled', 'false') == 'true'
        google_button_active = google_toggle_enabled and GOOGLE_OAUTH_ENABLED
        facebook_toggle_enabled = settings.get('facebook_login_enabled', 'false') == 'true'
        facebook_button_active = facebook_toggle_enabled and FACEBOOK_OAUTH_ENABLED
        
        # Determine background style safely
        background_image_css = ""
        try:
            if bg_image_type == 'upload' and bg_image_data:
                value = bg_image_data.strip()
                if value:
                    background_image_css = value if value.startswith('url(') else f"url({value})"
            elif bg_image_type == 'url' and bg_image_raw:
                value = bg_image_raw.strip()
                if value and value.lower() != 'none':
                    background_image_css = value if value.startswith('url(') else f"url({value})"
            elif bg_image_raw and bg_image_raw.strip() and bg_image_raw.strip().lower() != 'none':
                value = bg_image_raw.strip()
                background_image_css = value if value.startswith('url(') else f"url({value})"
        except Exception as e:
            print(f"Error processing background image: {e}")
            background_image_css = ""
        
        # Set final background style
        if background_image_css:
            background_style = f"background: {background_image_css} no-repeat center center fixed, linear-gradient(135deg, {bg_color}, #764ba2); background-size: cover;"
        else:
            background_style = f"background: linear-gradient(135deg, {bg_color}, #764ba2);"
            
        # Prepare the HTML response (legacy snippet; main template is defined below)
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>{page_title}</title>
          <style>
            body {{
              margin: 0;
              padding: 0;
              font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
              {background_style}
              min-height: 100vh;
              """
    except Exception as e:
        # If anything above fails, log it and return a very simple fallback page
        print(f"Error rendering /login page: {e}")
        return HTMLResponse(
            content="<h1>Login page error</h1><p>Please contact the administrator.</p>",
            status_code=500,
        )

    # Set up OAuth buttons based on settings
    google_button_active = google_toggle_enabled and GOOGLE_OAUTH_ENABLED
    facebook_button_active = facebook_toggle_enabled and FACEBOOK_OAUTH_ENABLED
    
    # Determine background style
    background_image_css = ""
    if bg_image_type == 'upload' and bg_image_data:
        value = bg_image_data.strip()
        if value:
            background_image_css = value if value.startswith('url(') else f"url({value})"
    elif bg_image_type == 'url':
        value = bg_image_raw.strip()
        if value and value.lower() != 'none':
            background_image_css = value if value.startswith('url(') else f"url({value})"
    # For compatibility with legacy data that stored CSS url(...) directly
    elif bg_image_raw and bg_image_raw.strip() and bg_image_raw.strip().lower() != 'none':
        value = bg_image_raw.strip()
        background_image_css = value if value.startswith('url(') else f"url({value})"
    
    if background_image_css:
        background_style = f"background: {background_image_css} no-repeat center center fixed, linear-gradient(135deg, {bg_color}, #764ba2); background-size: cover;"
    else:
        background_style = f"background: linear-gradient(135deg, {bg_color}, #764ba2);"

    # Main HTML template for the login page
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{page_title}</title>
  <style>
    body {{
      margin: 0;
      padding: 0;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      {background_style}
      min-height: 100;
      display: flex;
      justify-content: center;
      align-items: center;
    }}
    .page-layout {{
      width: min(1100px, calc(100% - 40px));
      display: flex;
      gap: 32px;
      flex-wrap: wrap;
      justify-content: center;
      align-items: stretch;
      margin: 48px auto;
    }}
    .card {{
      border-radius: 20px;
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.35);
      border: 1px solid rgba(255, 255, 255, 0.18);
      flex: 1 1 320px;
      max-width: 480px;
      background: rgba(255, 255, 255, 0.95);
      backdrop-filter: blur(10px);
    }}
    .form-card {{
      padding: 40px;
      text-align: center;
      color: #333;
    }}
    
    @media (max-width: 768px) {{
      .form-card {{
        padding: 32px 24px;
      }}
      .page-layout {{
        width: calc(100% - 32px);
        flex-direction: column;
        align-items: stretch;
        gap: 24px;
      }}
    }}
    
    @media (max-width: 640px) {{
      .card {{
        max-width: 100%;
      }}
      .page-layout {{
        margin: 24px auto;
      }}
    }}
    .form-card h1 {{
      margin-bottom: 30px;
      font-size: 28px;
      font-weight: 600;
      color: #2c3e50;
      margin-top: 0;
    }}
    .input-group {{
      margin-bottom: 10px;
      text-align: left;
    }}
    .input-group label {{
      display: block;
      margin-bottom: 8px;
      font-weight: 500;
      color: #555;
      font-size: 14px;
    }}
    input[type="email"] {{
      padding: 16px 20px;
      width: 100%;
      border: 2px solid #e1e8ed;
      border-radius: 12px;
      font-size: 16px;
      transition: all 0.3s ease;
      background: #f8f9fa;
      color: #333;
      box-sizing: border-box;
    }}
    input[type="email"]:focus {{
      outline: none;
      border-color: #3498db;
      background: white;
      box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
    }}
    .validation-message {{
      font-size: 13px;
      margin-top: 5px;
      min-height: 16px;
    }}
    .consent {{
      margin-top: 12px;
      text-align: left;
      font-size: 12px;
      color: #555;
      background: #f8f9ff;
      border: 1px solid #e6e8ff;
      border-radius: 10px;
      padding: 12px;
    }}
    .consent label {{
      display: flex;
      align-items: flex-start;
      gap: 10px;
      cursor: pointer;
      line-height: 1.4;
    }}
    .consent input[type="checkbox"] {{
      margin-top: 2px;
      width: 18px;
      height: 18px;
      accent-color: #667eea;
    }}
    .validation-message.invalid {{
      color: #dc3545;
    }}
    .validation-message.valid {{
      color: #28a745;
    }}
    button {{
      margin-top: 15px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 16px 20px;
      border: none;
      border-radius: 12px;
      width: 100%;
      cursor: pointer;
      font-size: 16px;
      font-weight: 600;
      transition: all 0.3s ease;
      box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
      box-sizing: border-box;
    }}
    button:hover {{
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
    }}
    button:disabled {{
      opacity: 0.6;
      cursor: not-allowed;
      transform: none;
    }}
    .social-login {{
      margin-top: 20px;
      padding-top: 20px;
      border-top: 1px solid #e1e8ed;
    }}
    .social-login p {{
      color: #666;
      font-size: 14px;
      margin-bottom: 15px;
    }}
    .social-button {{
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 12px;
      padding: 14px 20px;
      border: 2px solid #e1e8ed;
      border-radius: 12px;
      background: white;
      color: #333;
      text-decoration: none;
      font-weight: 600;
      transition: all 0.3s ease;
      margin-bottom: 10px;
      position: relative;
    }}
    .social-button.disabled {{
      opacity: 0.6;
      cursor: not-allowed;
      pointer-events: auto;
    }}
    .social-button.disabled:hover {{
      transform: none;
      box-shadow: none;
      background: white;
    }}
    .social-button .status-badge {{
      position: absolute;
      top: 10px;
      right: 10px;
      font-size: 11px;
      font-weight: 600;
      background: #f97316;
      color: white;
      padding: 2px 8px;
      border-radius: 999px;
      letter-spacing: 0.3px;
    }}
    .social-button:hover {{
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }}
    .social-button svg {{
      width: 20px;
      height: 20px;
    }}
    .social-button.google {{
      border-color: #db4437;
      color: #db4437;
    }}
    .social-button.google:hover {{
      background: #db4437;
      color: white;
    }}
    .social-button.google:hover svg path {{
      fill: white;
    }}
    .social-button.facebook {{
      border-color: #1877f2;
      color: #1877f2;
    }}
    .social-button.facebook:hover {{
      background: #1877f2;
      color: white;
    }}
    .social-button.facebook:hover svg {{
      fill: white;
    }}
    .oauth-warning {{
      margin-top: 10px;
      font-size: 13px;
      color: #b45309;
      text-align: center;
    }}
    .ad-card {{
      background: rgba(6, 11, 38, 0.92);
      color: white;
      padding: 0;
      border-radius: 24px;
      border: 1px solid rgba(255, 255, 255, 0.08);
      overflow: hidden;
    }}
    .ad-card + .ad-card {{
      margin-top: 24px;
    }}
    .ad-image-wrapper {{
      position: relative;
    }}
    .ad-image-wrapper img {{
      width: 100%;
      height: 320px;
      object-fit: cover;
      display: block;
    }}
    .ad-label {{
      position: absolute;
      top: 20px;
      left: 20px;
      background: rgba(0, 0, 0, 0.65);
      color: white;
      padding: 6px 14px;
      border-radius: 999px;
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    .ad-content {{
      padding: 24px 30px 32px;
    }}
    .ad-content h2 {{
      margin: 12px 0;
      font-size: 26px;
      color: white;
      line-height: 1.3;
    }}
    .ad-description {{
      margin: 0;
      color: #dbeafe;
      line-height: 1.6;
      font-size: 15px;
    }}
    .ad-timeframe {{
      margin: 0;
      color: #fcd34d;
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    @media (max-width: 640px) {{
      .card {{
        max-width: 100%;
      }}
      .page-layout {{
        margin: 24px auto;
      }}
      .ad-image-wrapper img {{
        height: 220px;
      }}
      .ad-content {{
        padding: 20px 18px 24px;
      }}
      .ad-content h2 {{
        font-size: 22px;
      }}
    }}
    .message {{
      margin-top: 20px;
      padding: 12px 16px;
      border-radius: 8px;
      font-size: 14px;
      font-weight: 500;
      min-height: 20px;
    }}
  </style>
</head>
<body>
  <div class="page-layout">
    <div class="card form-card">
      {ad_section_html}
      <h1>{page_title}</h1>
      <div class="input-group">
        <label for="email">Email Address</label>
        <input type="email" id="email" placeholder="Enter your email address" required>
        <div id="validation-message" class="validation-message"></div>
      </div>
      <div class="consent">
        <label for="consent">
          <input type="checkbox" id="consent">
          <span>
            By providing your email address, you agree and consent that it may be used for marketing purposes, including but not limited to receiving promotional emails, newsletters, offers, and updates related to our products and services. You may unsubscribe at any time using the link provided in each email.
          </span>
        </label>
      </div>
      <div id="consent-validation" class="validation-message"></div>
      <button type="button" id="login-btn" disabled>{button_text}</button>
      <div class="message" id="message"></div>
      
    """
    
    show_social_logins = google_toggle_enabled or facebook_toggle_enabled
    if show_social_logins:
        html += """
    <div class="social-login">
      <p>Or continue with:</p>
"""
        if google_toggle_enabled:
            google_href = "/auth/google/login" if google_button_active else "#"
            google_extra_class = "" if google_button_active else " disabled"
            google_disabled_attr = "" if google_button_active else ' data-disabled="true"'
            google_status_badge = "" if google_button_active else '<span class="status-badge">Offline</span>'
            html += f"""
      <a href="{google_href}" class="social-button google{google_extra_class}"{google_disabled_attr}>
        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
          <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
          <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
          <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
        </svg>
        Continue with Google
        {google_status_badge}
      </a>
"""
        if facebook_toggle_enabled:
            facebook_href = "/auth/facebook/login" if facebook_button_active else "#"
            facebook_extra_class = "" if facebook_button_active else " disabled"
            facebook_disabled_attr = "" if facebook_button_active else ' data-disabled="true"'
            facebook_status_badge = "" if facebook_button_active else '<span class="status-badge">Offline</span>'
            html += f"""
      <a href="{facebook_href}" class="social-button facebook{facebook_extra_class}"{facebook_disabled_attr}>
        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="#1877f2">
          <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
        </svg>
        Continue with Facebook
        {facebook_status_badge}
      </a>
"""
        html += """
    </div>
"""
        if google_toggle_enabled and not google_button_active:
            html += """
    <div class="oauth-warning">Google login is temporarily unavailable. Please contact the administrator.</div>
"""
        if facebook_toggle_enabled and not facebook_button_active:
            html += """
    <div class="oauth-warning">Facebook login is temporarily unavailable. Please contact the administrator.</div>
"""
    
    html += f"""
    </div>
  </div>
  
  <script>
    // ✅ domain HTTPS - Use production URL, or local origin for development
    const API_BASE = window.location.origin;
  
    var GATEWAY_IP = "{GATEWAY_IP}";
    var HOTSPOT_USER = "{HOTSPOT_USER}";
    var HOTSPOT_PASS = "{HOTSPOT_PASS}";
    var FINAL_REDIRECT = "{DST_URL}";
  
    var emailInput = document.getElementById("email");
    var validationMessage = document.getElementById("validation-message");
    var loginBtn = document.getElementById("login-btn");
    var consentCheckbox = document.getElementById("consent");
    var consentValidation = document.getElementById("consent-validation");
  
    console.log("Elements found - emailInput:", !!emailInput, "loginBtn:", !!loginBtn, "consentCheckbox:", !!consentCheckbox);
  
    if (!emailInput || !loginBtn || !consentCheckbox) {{
      console.error("Required elements not found!");
      alert("Error: Required form elements not found. Please refresh the page.");
    }} else {{
      console.log("Initial email value:", emailInput.value);
      console.log("Initial consent checked:", consentCheckbox.checked);
    
      var emailRegex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
    
      function updateButtonState() {{
        try {{
          if (!emailInput || !loginBtn || !consentCheckbox) {{
            console.error("Elements missing in updateButtonState");
            return;
          }}
          
          var email = emailInput.value.trim();
          var emailValid = emailRegex.test(email);
          var consentChecked = consentCheckbox.checked;
          
          console.log("updateButtonState - Email:", email, "Valid:", emailValid, "Consent:", consentChecked);
          
          if (validationMessage) {{
            if (!emailValid) {{
              validationMessage.textContent = "That's not an email format!";
              validationMessage.className = "validation-message invalid";
            }} else {{
              validationMessage.textContent = "✓ Looks good!";
              validationMessage.className = "validation-message valid";
            }}
          }}
          
          if (consentValidation) {{
            if (consentChecked) {{
              consentValidation.textContent = "✓ Thanks for subscribing!";
              consentValidation.className = "validation-message valid";
            }} else {{
              consentValidation.textContent = "Please check the box to agree to receive our newsletter";
              consentValidation.className = "validation-message invalid";
            }}
          }}
          
          var shouldEnable = emailValid && consentChecked;
          loginBtn.disabled = !shouldEnable;
          console.log("Button state updated - shouldEnable:", shouldEnable, "disabled:", loginBtn.disabled);
          
          // Force enable if email and consent are valid (safety check)
          if (emailValid && consentChecked && loginBtn.disabled) {{
            console.warn("Button should be enabled but is disabled - forcing enable");
            loginBtn.disabled = false;
          }}
        }} catch (error) {{
          console.error("Error in updateButtonState:", error);
          console.error(error.stack);
        }}
      }}

      emailInput.addEventListener("input", updateButtonState);
      consentCheckbox.addEventListener("change", updateButtonState);
      
      // Initialize button state on page load - try multiple times to ensure it works
      setTimeout(updateButtonState, 100);
      setTimeout(updateButtonState, 500);
      
      // Also run when DOM is fully ready
      if (document.readyState === "loading") {{
        document.addEventListener("DOMContentLoaded", updateButtonState);
      }} else {{
        updateButtonState();
      }}
      
      console.log("Initial button state - disabled:", loginBtn.disabled);
    
      // Login function - make it globally accessible
      async function handleLogin() {{
        console.log("=== LOGIN FUNCTION CALLED ===");
        try {{
          var email = emailInput.value.trim();
          var msg = document.getElementById("message");
          
          console.log("Email:", email);
          console.log("Consent checked:", consentCheckbox.checked);
          console.log("API_BASE:", API_BASE);
      
          if (!emailRegex.test(email)) {{
            msg.textContent = "Please enter a valid email.";
            msg.className = "message error";
            return;
          }}
          if (!consentCheckbox.checked) {{
            msg.textContent = "Please check the box to agree to receive our newsletter";
            msg.className = "message error";
            return;
          }}
      
          msg.textContent = "Saving email...";
          msg.className = "message";
          console.log("Attempting to save email...");
      
          try {{
            var emailObj = {{}};
            emailObj.email = email;
            emailObj.consent = true;
            var apiUrl = API_BASE + "/save_trial_email";
            console.log("Fetching:", apiUrl);
            console.log("Payload:", JSON.stringify(emailObj));
            
            var response = await fetch(apiUrl, {{
              method: "POST",
              headers: {{"Content-Type": "application/json"}},
              body: JSON.stringify(emailObj)
            }});
            console.log("Response status:", response.status);
            if (!response.ok) {{
              var errorText = await response.text();
              console.error("Failed to save email:", response.status, errorText);
            }} else {{
              var result = await response.json();
              console.log("Email saved successfully:", result);
            }}
          }} catch (error) {{
            console.error("Error saving email:", error);
            // Continue anyway - don't block the login
          }}
      
          msg.textContent = "Connecting to WiFi...";
          msg.className = "message success";
      
          var loginUrl = "http://" + GATEWAY_IP + "/login?username=" + HOTSPOT_USER +
            "&password=" + HOTSPOT_PASS +
            "&dst=" + encodeURIComponent(FINAL_REDIRECT);
          console.log("Redirecting to:", loginUrl);
      
          setTimeout(function() {{
            window.location.href = loginUrl;
          }}, 1000);
        }} catch (error) {{
          console.error("Error in login function:", error);
          alert("An error occurred: " + error.message + "\\nCheck console for details.");
        }}
      }}
      
      // Make it globally accessible
      window.login = handleLogin;
      
      console.log("Login function registered. API_BASE:", API_BASE);
      console.log("Login function available:", typeof window.login);
      
      // Attach event listener to button
      function handleButtonClick(e) {{
        console.log("=== BUTTON CLICKED ===");
        console.log("Button disabled:", loginBtn.disabled);
        console.log("Email:", emailInput.value);
        console.log("Consent:", consentCheckbox.checked);
        
        // Always allow click, check validation inside
        e.preventDefault();
        e.stopPropagation();
        
        // Re-check validation
        var email = emailInput.value.trim();
        var emailValid = emailRegex.test(email);
        var consentChecked = consentCheckbox.checked;
        
        if (!emailValid || !consentChecked) {{
          console.warn("Validation failed - Email valid:", emailValid, "Consent:", consentChecked);
          alert("Please enter a valid email and check the consent box.");
          updateButtonState();
          return;
        }}
        
        console.log("Validation passed, calling handleLogin...");
        handleLogin();
      }}
      
      loginBtn.addEventListener("click", handleButtonClick);
      loginBtn.onclick = handleButtonClick;
      
      // Handle disabled social buttons
      var disabledButtons = document.querySelectorAll('.social-button[data-disabled="true"]');
      for (var i = 0; i < disabledButtons.length; i++) {{
        var button = disabledButtons[i];
        button.addEventListener("click", function(event) {{
          event.preventDefault();
          var provider = button.classList.contains("google") ? "Google" : "Facebook";
          alert(provider + " login is not configured yet. Please contact the administrator.");
        }});
      }}
    }}
  </script>
  
</body>
</html>
    """
    return HTMLResponse(content=html)

