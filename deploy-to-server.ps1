# ============================================
# AUTO-UPLOAD SCRIPT FOR DIGITALOCEAN SERVER
# Uploads local code to DigitalOcean droplet
# ============================================

param(
    [string]$ServerIP = "146.190.90.47",
    [string]$ServerUser = "root",
    [string]$ServerPath = "/var/www/wifi_hotspot",
    [string]$SSHKey = "",
    [switch]$RunDeploy = $false,
    [switch]$SkipBackup = $false
)

# Colors for output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-ColorOutput Green "============================================"
Write-ColorOutput Green "  AUTO-UPLOAD TO DIGITALOCEAN SERVER"
Write-ColorOutput Green "============================================"
Write-Output ""

# Check if OpenSSH is available
$scpPath = Get-Command scp -ErrorAction SilentlyContinue
if (-not $scpPath) {
    Write-ColorOutput Red "❌ ERROR: SCP (OpenSSH) is not found!"
    Write-Output "Please install OpenSSH Client:"
    Write-Output "  Settings > Apps > Optional Features > OpenSSH Client"
    Write-Output ""
    Write-Output "Or run in PowerShell (as Administrator):"
    Write-Output "  Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0"
    exit 1
}

Write-ColorOutput Green "✅ SCP found: $($scpPath.Source)"
Write-Output ""

# Build SSH/SCP command prefix
$sshPrefix = if ($SSHKey) {
    "-i `"$SSHKey`""
} else {
    ""
}

# Test SSH connection
$serverAddr = $ServerUser + "@" + $ServerIP
Write-ColorOutput Cyan "🔍 Testing SSH connection to $serverAddr..."
$testConnection = ssh $sshPrefix.Split(' ') -o ConnectTimeout=5 -o BatchMode=yes $serverAddr "echo 'Connection successful'" 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput Yellow "⚠️  SSH key authentication failed or connection timeout"
    Write-Output "You may need to:"
    Write-Output "  1. Enter password when prompted"
    Write-Output "  2. Or use -SSHKey parameter to specify your SSH key path"
    Write-Output ""
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        exit 1
    }
} else {
    Write-ColorOutput Green "✅ SSH connection successful!"
}
Write-Output ""

# Files to upload (exclude unnecessary files)
$filesToUpload = @(
    "app.py",
    "requirements.txt",
    "gunicorn_config.py",
    "monitor.py",
    "deploy-zero-downtime.sh",
    "deploy.sh",
    "login.html"
)

# Directories to upload
$dirsToUpload = @(
    "img"
)

# Files to exclude
$excludePatterns = @(
    "__pycache__",
    "*.pyc",
    "*.pyo",
    ".env",
    ".git",
    "*.log",
    ".DS_Store",
    "Thumbs.db"
)

Write-ColorOutput Cyan "📦 Preparing files for upload..."
Write-Output ""

# Check if files exist
$missingFiles = @()
foreach ($file in $filesToUpload) {
    if (-not (Test-Path $file)) {
        $missingFiles += $file
    }
}

foreach ($dir in $dirsToUpload) {
    if (-not (Test-Path $dir)) {
        $missingFiles += $dir
    }
}

if ($missingFiles.Count -gt 0) {
    Write-ColorOutput Yellow "⚠️  Warning: Some files/directories are missing:"
    foreach ($file in $missingFiles) {
        Write-Output "  - $file"
    }
    Write-Output ""
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        exit 1
    }
}

# Create backup on server (optional)
if (-not $SkipBackup) {
    Write-ColorOutput Cyan "💾 Creating backup on server..."
    $backupCmd = "mkdir -p $ServerPath/backups && cd $ServerPath && tar -czf backups/backup_$(date +%Y%m%d_%H%M%S).tar.gz *.py *.txt *.sh *.html img/ 2>/dev/null || true"
    
    if ($SSHKey) {
        ssh -i "$SSHKey" $serverAddr $backupCmd
    } else {
        ssh $serverAddr $backupCmd
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput Green "✅ Backup created"
    } else {
        Write-ColorOutput Yellow "⚠️  Backup may have failed (continuing anyway)"
    }
    Write-Output ""
}

# Upload files
Write-ColorOutput Cyan "📤 Uploading files to server..."
Write-Output ""

$uploadSuccess = $true
$uploadedCount = 0

# Upload individual files
foreach ($file in $filesToUpload) {
    if (Test-Path $file) {
        Write-Output "  Uploading: $file"
        $scpArgs = if ($SSHKey) {
            "-i", "`"$SSHKey`"", "`"$file`"", "`"$ServerUser@${ServerIP}:${ServerPath}/`""
        } else {
            "`"$file`"", "`"$ServerUser@${ServerIP}:${ServerPath}/`""
        }
        
        & scp $scpArgs 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            $uploadedCount++
            Write-ColorOutput Green "    ✅ $file uploaded"
        } else {
            Write-ColorOutput Red "    ❌ Failed to upload $file"
            $uploadSuccess = $false
        }
    }
}

# Upload directories
foreach ($dir in $dirsToUpload) {
    if (Test-Path $dir) {
        Write-Output "  Uploading directory: $dir/"
        $scpArgs = if ($SSHKey) {
            "-i", "`"$SSHKey`"", "-r", "`"$dir`"", "`"$ServerUser@${ServerIP}:${ServerPath}/`""
        } else {
            "-r", "`"$dir`"", "`"$ServerUser@${ServerIP}:${ServerPath}/`""
        }
        
        & scp $scpArgs 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            $uploadedCount++
            Write-ColorOutput Green "    ✅ $dir/ uploaded"
        } else {
            Write-ColorOutput Red "    ❌ Failed to upload $dir/"
            $uploadSuccess = $false
        }
    }
}

Write-Output ""

if (-not $uploadSuccess) {
    Write-ColorOutput Red "❌ Some files failed to upload!"
    Write-Output "Please check your connection and try again."
    exit 1
}

Write-ColorOutput Green "✅ Successfully uploaded $uploadedCount items"
Write-Output ""

# Set permissions on server
Write-ColorOutput Cyan "🔧 Setting file permissions on server..."
$permCmd = "cd $ServerPath && chmod +x *.sh 2>/dev/null; chmod 644 *.py *.txt *.html 2>/dev/null; echo 'Permissions set'"

if ($SSHKey) {
    ssh -i "$SSHKey" $serverAddr $permCmd | Out-Null
} else {
    ssh $serverAddr $permCmd | Out-Null
}

if ($LASTEXITCODE -eq 0) {
    Write-ColorOutput Green "✅ Permissions set"
} else {
    Write-ColorOutput Yellow "⚠️  Failed to set permissions (may need manual fix)"
}
Write-Output ""

# Run deployment script if requested
if ($RunDeploy) {
    Write-ColorOutput Cyan "🚀 Running deployment script on server..."
    Write-Output ""
    
    $deployCmd = "cd $ServerPath; bash deploy-zero-downtime.sh"
    
    if ($SSHKey) {
        ssh -i "$SSHKey" $serverAddr $deployCmd
    } else {
        ssh $serverAddr $deployCmd
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput Green "✅ Deployment completed successfully!"
    } else {
        Write-ColorOutput Red "❌ Deployment script returned an error"
        Write-Output "Please check the output above for details."
    }
} else {
    Write-ColorOutput Yellow "ℹ️  Deployment script not run (use -RunDeploy to auto-deploy)"
    Write-Output ""
    Write-Output "To deploy manually, SSH to server and run:"
    Write-Output "  cd $ServerPath"
    Write-Output "  bash deploy-zero-downtime.sh"
}

Write-Output ""
Write-ColorOutput Green "============================================"
Write-ColorOutput Green "  UPLOAD COMPLETED!"
Write-ColorOutput Green "============================================"
Write-Output ""
Write-Host 'Server:' $serverAddr
Write-Host 'Path:' $ServerPath
Write-Output ""

