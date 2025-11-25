# ============================================
# DEPLOYMENT CONFIGURATION
# Edit these values to match your server setup
# ============================================

# Server connection details
$script:ServerIP = "146.190.90.47"
$script:ServerUser = "root"
$script:ServerPath = "/var/www/wifi_hotspot"

# SSH Key path (leave empty to use password authentication)
# Example: "C:\Users\YourName\.ssh\id_rsa"
$script:SSHKey = ""

# Auto-run deployment script after upload?
# Set to $true to automatically deploy after upload
# Set to $false to only upload files (deploy manually later)
$script:AutoDeploy = $false

# Skip backup before upload?
$script:SkipBackup = $false

# ============================================
# Load this config in deploy script:
# . .\deploy-config.ps1
# ============================================

