#!/bin/bash
# UPLOAD ALL FILES TO SERVER - ONE COMMAND

PASSWORD="Fujimori6Riho"
SERVER="root@146.190.90.47"
REMOTE_PATH="/var/www/wifi_hotspot"

echo "========================================"
echo "  UPLOADING ALL FILES TO SERVER"
echo "========================================"
echo ""

# Check for sshpass
HAS_SSHPASS=0
if command -v sshpass &> /dev/null; then
    HAS_SSHPASS=1
    echo "✓ Using sshpass (password will be auto-entered)"
else
    echo "⚠ sshpass not found - you'll enter password manually"
    echo "  Password: $PASSWORD"
    echo ""
    echo "To install sshpass (optional):"
    echo "  Ubuntu/WSL: sudo apt-get install sshpass"
    echo "  Git Bash: Download from https://github.com/keimpx/sshpass-windows"
    echo ""
fi

echo "Starting upload..."
echo ""

# Upload function
upload() {
    local src=$1
    local is_dir=${2:-0}
    
    if [ "$is_dir" = "1" ]; then
        [ ! -d "$src" ] && echo "⚠ Skipping $src (not found)" && return
    else
        [ ! -f "$src" ] && echo "⚠ Skipping $src (not found)" && return
    fi
    
    printf "Uploading: %-30s " "$src"
    
    if [ "$HAS_SSHPASS" = "1" ]; then
        if [ "$is_dir" = "1" ]; then
            sshpass -p "$PASSWORD" scp -r -o StrictHostKeyChecking=no "$src" "${SERVER}:${REMOTE_PATH}/" 2>/dev/null
        else
            sshpass -p "$PASSWORD" scp -o StrictHostKeyChecking=no "$src" "${SERVER}:${REMOTE_PATH}/" 2>/dev/null
        fi
    else
        if [ "$is_dir" = "1" ]; then
            scp -r -o StrictHostKeyChecking=no "$src" "${SERVER}:${REMOTE_PATH}/" 2>/dev/null
        else
            scp -o StrictHostKeyChecking=no "$src" "${SERVER}:${REMOTE_PATH}/" 2>/dev/null
        fi
    fi
    
    if [ $? -eq 0 ]; then
        echo "✓ OK"
    else
        echo "✗ FAILED"
    fi
}

# Upload all files
upload "app.py"
upload "requirements.txt"
upload "gunicorn_config.py"
upload "monitor.py"
upload "deploy-zero-downtime.sh"
upload "deploy.sh"
upload "login.html"
upload "img" 1

# Set permissions
echo ""
echo "Setting file permissions..."
if [ "$HAS_SSHPASS" = "1" ]; then
    sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER" "cd $REMOTE_PATH && chmod +x *.sh 2>/dev/null; chmod 644 *.py *.txt *.html 2>/dev/null" 2>/dev/null
else
    ssh -o StrictHostKeyChecking=no "$SERVER" "cd $REMOTE_PATH && chmod +x *.sh 2>/dev/null; chmod 644 *.py *.txt *.html 2>/dev/null" 2>/dev/null
fi

echo ""
echo "========================================"
echo "  ✓ UPLOAD COMPLETE!"
echo "========================================"
echo ""
echo "All files uploaded to: $REMOTE_PATH"
echo ""
echo "Next step: Deploy the code"
echo "  ssh $SERVER"
echo "  cd $REMOTE_PATH"
echo "  bash deploy-zero-downtime.sh"
echo ""

