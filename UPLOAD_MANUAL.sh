#!/bin/bash
# Manual upload script - Run this in Git Bash or WSL

PASSWORD="Fujimori6Riho"
SERVER="root@146.190.90.47"
PATH="/var/www/wifi_hotspot"

echo "========================================"
echo "  UPLOADING ALL FILES"
echo "========================================"
echo ""

# Install sshpass if not available (for Git Bash/WSL)
if ! command -v sshpass &> /dev/null; then
    echo "Installing sshpass..."
    # For Ubuntu/WSL: sudo apt-get install sshpass -y
    # For Git Bash: Download from https://github.com/keimpx/sshpass-windows
    echo "Please install sshpass first, or enter password manually for each file"
fi

# Upload files
sshpass -p "$PASSWORD" scp app.py "$SERVER:$PATH/"
sshpass -p "$PASSWORD" scp requirements.txt "$SERVER:$PATH/"
sshpass -p "$PASSWORD" scp gunicorn_config.py "$SERVER:$PATH/"
sshpass -p "$PASSWORD" scp monitor.py "$SERVER:$PATH/"
sshpass -p "$PASSWORD" scp deploy-zero-downtime.sh "$SERVER:$PATH/"
sshpass -p "$PASSWORD" scp deploy.sh "$SERVER:$PATH/"
sshpass -p "$PASSWORD" scp login.html "$SERVER:$PATH/"
sshpass -p "$PASSWORD" scp -r img "$SERVER:$PATH/"

echo ""
echo "UPLOAD COMPLETE!"

