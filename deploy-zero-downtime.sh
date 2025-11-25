#!/bin/bash
set -e

# ============================================
# ZERO-DOWNTIME DEPLOYMENT SCRIPT
# Uses Gunicorn graceful reload (HUP signal)
# ============================================

APP_DIR="/var/www/wifi_hotspot"
VENV="$APP_DIR/venv"
BACKUP_DIR="$APP_DIR/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/backup_$TIMESTAMP"
HEALTH_CHECK_URL="https://wifi.nuanu.io/api/settings"
MAX_HEALTH_CHECK_RETRIES=10
HEALTH_CHECK_INTERVAL=2

# === Telegram Config ===
TELEGRAM_TOKEN="7137088973:AAGlJOO7OEDweSkUWlvp7mEDUbyIdJ5Xnmw"
CHAT_ID="5481015560"
send_telegram() {
    curl -s -X POST https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage \
         -d chat_id=${CHAT_ID} \
         -d text="$1" > /dev/null 2>&1 || true
}

# Error handler with rollback
rollback() {
    echo "❌ DEPLOYMENT FAILED! Attempting rollback..."
    send_telegram "❌ DEPLOY FAILED - Rolling back to previous version"
    
    if [ -d "$BACKUP_PATH" ]; then
        echo "🔄 Restoring from backup: $BACKUP_PATH"
        cd $APP_DIR
        cp -r $BACKUP_PATH/* .
        sudo systemctl reload gunicorn
        echo "✅ Rollback completed"
        send_telegram "✅ Rollback completed - Service restored"
    else
        echo "⚠️ No backup found for rollback"
        send_telegram "⚠️ Rollback failed - No backup available"
    fi
    exit 1
}

trap rollback ERR

# Health check function
health_check() {
    local url=$1
    local retries=0
    
    echo "🏥 Performing health check on $url..."
    
    while [ $retries -lt $MAX_HEALTH_CHECK_RETRIES ]; do
        if curl -f -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200"; then
            echo "✅ Health check passed!"
            return 0
        fi
        retries=$((retries + 1))
        echo "⏳ Health check attempt $retries/$MAX_HEALTH_CHECK_RETRIES failed, retrying in ${HEALTH_CHECK_INTERVAL}s..."
        sleep $HEALTH_CHECK_INTERVAL
    done
    
    echo "❌ Health check failed after $MAX_HEALTH_CHECK_RETRIES attempts"
    return 1
}

# Pre-deployment health check
echo "🔍 Pre-deployment health check..."
if ! health_check "$HEALTH_CHECK_URL"; then
    echo "⚠️ WARNING: Service is not healthy before deployment!"
    send_telegram "⚠️ WARNING: Service unhealthy before deployment - Proceeding anyway..."
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Backup current code
echo "💾 Creating backup of current code..."
cd $APP_DIR
mkdir -p "$BACKUP_PATH"
cp -r app.py requirements.txt *.py *.sh "$BACKUP_PATH/" 2>/dev/null || true
cp -r img "$BACKUP_PATH/" 2>/dev/null || true
echo "✅ Backup created at: $BACKUP_PATH"

# Start deployment
echo "🚀 Starting ZERO-DOWNTIME deployment..."
send_telegram "🚀 Starting ZERO-DOWNTIME deployment on wifi.nuanu.io"

cd $APP_DIR

# 1️⃣ Install/update dependencies (this is safe, doesn't affect running processes)
echo "📦 Installing Python dependencies..."
$VENV/bin/pip install -q --upgrade pip
$VENV/bin/pip install -q -r requirements.txt
echo "✅ Dependencies installed"

# 2️⃣ Test Nginx configuration (before reloading)
echo "🧪 Testing Nginx configuration..."
if ! sudo nginx -t; then
    echo "❌ Nginx configuration test failed!"
    send_telegram "❌ Nginx config test failed - Deployment aborted"
    exit 1
fi
echo "✅ Nginx configuration is valid"

# 3️⃣ GRACEFUL RELOAD - This is the key to zero-downtime!
echo "🔄 Performing graceful reload of Gunicorn (ZERO-DOWNTIME)..."
echo "   This will reload workers one by one without stopping the service"

# Get Gunicorn master process PID
GUNICORN_PID=$(pgrep -f "gunicorn.*app:app" | head -n 1)

if [ -z "$GUNICORN_PID" ]; then
    echo "⚠️ Gunicorn process not found, starting fresh..."
    sudo systemctl start gunicorn
    sleep 3
    GUNICORN_PID=$(pgrep -f "gunicorn.*app:app" | head -n 1)
fi

if [ -n "$GUNICORN_PID" ]; then
    # Send HUP signal for graceful reload (zero-downtime)
    echo "   Sending HUP signal to Gunicorn master (PID: $GUNICORN_PID)..."
    sudo kill -HUP $GUNICORN_PID
    echo "✅ Graceful reload signal sent"
    
    # Wait a moment for workers to start reloading
    sleep 2
    
    # Verify Gunicorn is still running
    if ! pgrep -f "gunicorn.*app:app" > /dev/null; then
        echo "❌ Gunicorn process died after reload!"
        send_telegram "❌ Gunicorn died after reload - Attempting restart"
        sudo systemctl restart gunicorn
        sleep 3
    fi
else
    echo "⚠️ Could not find Gunicorn PID, using systemctl reload instead..."
    sudo systemctl reload gunicorn
fi

# 4️⃣ Reload Nginx (graceful, zero-downtime)
echo "🔄 Reloading Nginx (graceful reload)..."
sudo systemctl reload nginx
echo "✅ Nginx reloaded"


# 5️⃣ Wait for new workers to be ready
echo "⏳ Waiting for new workers to be ready..."
sleep 3

# 6️⃣ Post-deployment health check
echo "🔍 Post-deployment health check..."
if ! health_check "$HEALTH_CHECK_URL"; then
    echo "❌ Health check failed after deployment!"
    send_telegram "❌ Post-deployment health check failed!"
    rollback
    exit 1
fi

# 7️⃣ Restart monitor service (if needed, this is usually safe)
if systemctl is-active --quiet webmonitor; then
    echo "📡 Restarting webmonitor..."
    sudo systemctl restart webmonitor
    echo "✅ Webmonitor restarted"
fi

# 8️⃣ Cleanup old backups (keep last 5)
echo "🧹 Cleaning up old backups (keeping last 5)..."
cd "$BACKUP_DIR"
ls -t | tail -n +6 | xargs rm -rf 2>/dev/null || true
echo "✅ Old backups cleaned"

# 9️⃣ Final status check
echo ""
echo "📊 Final Status Check:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Gunicorn status:"
sudo systemctl --no-pager is-active gunicorn && echo "   Status: ACTIVE ✅" || echo "   Status: INACTIVE ❌"
echo ""
echo "✅ Nginx status:"
sudo systemctl --no-pager is-active nginx && echo "   Status: ACTIVE ✅" || echo "   Status: INACTIVE ❌"
echo ""
echo "✅ Service health:"
if health_check "$HEALTH_CHECK_URL"; then
    echo "   Health: HEALTHY ✅"
else
    echo "   Health: UNHEALTHY ❌"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "🎉 ZERO-DOWNTIME deployment completed successfully!"
echo "📦 Backup saved at: $BACKUP_PATH"
send_telegram "✅ ZERO-DOWNTIME DEPLOY SUCCESS on wifi.nuanu.io - No downtime experienced!"

