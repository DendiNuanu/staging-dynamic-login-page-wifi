#!/bin/bash
# Upload all missing files to server

PASSWORD="Fujimori6Riho"
SERVER="root@146.190.90.47"
REMOTE_PATH="/var/www/wifi_hotspot"

echo "========================================"
echo "  UPLOADING MISSING FILES"
echo "========================================"
echo ""

# Check if sshpass is available
if command -v sshpass &> /dev/null; then
    USE_SSHPASS=1
    echo "Using sshpass for password authentication"
else
    USE_SSHPASS=0
    echo "sshpass not found - you will enter password for each file"
    echo "Password: $PASSWORD"
fi

echo ""

# Function to upload file
upload_file() {
    local file=$1
    local is_dir=$2
    
    if [ ! -f "$file" ] && [ "$is_dir" != "1" ]; then
        echo "Skipping $file (not found)"
        return
    fi
    
    if [ "$is_dir" = "1" ] && [ ! -d "$file" ]; then
        echo "Skipping $file (directory not found)"
        return
    fi
    
    echo -n "Uploading: $file ... "
    
    if [ "$USE_SSHPASS" = "1" ]; then
        if [ "$is_dir" = "1" ]; then
            sshpass -p "$PASSWORD" scp -r "$file" "${SERVER}:${REMOTE_PATH}/" 2>/dev/null
        else
            sshpass -p "$PASSWORD" scp "$file" "${SERVER}:${REMOTE_PATH}/" 2>/dev/null
        fi
    else
        if [ "$is_dir" = "1" ]; then
            scp -r "$file" "${SERVER}:${REMOTE_PATH}/" 2>/dev/null
        else
            scp "$file" "${SERVER}:${REMOTE_PATH}/" 2>/dev/null
        fi
    fi
    
    if [ $? -eq 0 ]; then
        echo "OK"
    else
        echo "FAILED"
    fi
}

# Upload missing files
upload_file "gunicorn_config.py" 0
upload_file "deploy-zero-downtime.sh" 0
upload_file "login.html" 0
upload_file "img" 1

# Set execute permission on deploy script
echo ""
echo "Setting permissions..."
if [ "$USE_SSHPASS" = "1" ]; then
    sshpass -p "$PASSWORD" ssh "$SERVER" "chmod +x ${REMOTE_PATH}/deploy-zero-downtime.sh" 2>/dev/null
else
    ssh "$SERVER" "chmod +x ${REMOTE_PATH}/deploy-zero-downtime.sh" 2>/dev/null
fi

echo ""
echo "========================================"
echo "  UPLOAD COMPLETE!"
echo "========================================"
echo ""
echo "Files uploaded:"
echo "  - gunicorn_config.py"
echo "  - deploy-zero-downtime.sh"
echo "  - login.html"
echo "  - img/ directory"
echo ""

