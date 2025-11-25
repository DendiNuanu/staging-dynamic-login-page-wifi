#!/bin/bash
set -e

APP_DIR="/var/www/wifi_hotspot"
VENV="$APP_DIR/venv"

# === Telegram Config ===
TELEGRAM_TOKEN="7137088973:AAGlJOO7OEDweSkUWlvp7mEDUbyIdJ5Xnmw"
CHAT_ID="5481015560"
send_telegram() {
    curl -s -X POST https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage \
         -d chat_id=${CHAT_ID} \
         -d text="$1"
}

# Trap error
trap 'send_telegram "❌ DEPLOY FAILED at step: $BASH_COMMAND"' ERR

echo "🚀 Starting deployment..."
send_telegram "🚀 Starting deployment on wifi.nuanu.io"

cd $APP_DIR

# 1️⃣ Install dependencies
echo "📦 Installing Python dependencies..."
$VENV/bin/pip install -r requirements.txt

# 2️⃣ GRACEFUL RELOAD - Zero-downtime deployment
echo "🔄 Performing graceful reload of Gunicorn (ZERO-DOWNTIME)..."
# Use reload instead of restart for zero-downtime
sudo systemctl daemon-reexec
sudo systemctl enable gunicorn

# Try graceful reload first (sends HUP signal)
if systemctl is-active --quiet gunicorn; then
    echo "   Service is running, performing graceful reload..."
    sudo systemctl reload gunicorn || sudo systemctl restart gunicorn
else
    echo "   Service not running, starting fresh..."
    sudo systemctl start gunicorn
fi

# 3️⃣ Test & reload Nginx
echo "🧪 Testing Nginx..."
sudo nginx -t
sudo systemctl reload nginx

# 4️⃣ Restart monitor service
echo "📡 Restarting webmonitor..."
sudo systemctl restart webmonitor

# 5️⃣ Status singkat
echo "✅ Gunicorn status:"
sudo systemctl --no-pager --full status gunicorn | head -n 10
echo "✅ Webmonitor status:"
sudo systemctl --no-pager --full status webmonitor | head -n 10

echo "🎉 Deployment completed successfully!"
send_telegram "✅ DEPLOY SUCCESS on wifi.nuanu.io"

