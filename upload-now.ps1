# Upload script with better error handling
param(
    [string]$ServerIP = "146.190.90.47",
    [string]$ServerUser = "root",
    [string]$ServerPath = "/var/www/wifi_hotspot",
    [string]$SSHKey = ""
)

$serverAddr = "$ServerUser@$ServerIP"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  UPLOADING TO DIGITALOCEAN SERVER" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Check if SSH key exists
if (-not $SSHKey) {
    $defaultKey = "$env:USERPROFILE\.ssh\id_rsa"
    if (Test-Path $defaultKey) {
        $SSHKey = $defaultKey
        Write-Host "Found SSH key: $SSHKey" -ForegroundColor Cyan
    }
}

# Files to upload
$files = @("app.py", "requirements.txt", "gunicorn_config.py", "monitor.py", "deploy-zero-downtime.sh", "deploy.sh")

# Check which files exist
$filesToUpload = @()
foreach ($file in $files) {
    if (Test-Path $file) {
        $filesToUpload += $file
    } else {
        Write-Host "Warning: $file not found, skipping..." -ForegroundColor Yellow
    }
}

if ($filesToUpload.Count -eq 0) {
    Write-Host "No files to upload!" -ForegroundColor Red
    exit 1
}

Write-Host "Files to upload: $($filesToUpload.Count)" -ForegroundColor Cyan
Write-Host ""

# Build SCP command prefix
$scpArgs = @()
if ($SSHKey -and (Test-Path $SSHKey)) {
    $scpArgs += "-i"
    $scpArgs += $SSHKey
    Write-Host "Using SSH key authentication" -ForegroundColor Green
} else {
    Write-Host "Using password authentication" -ForegroundColor Yellow
    Write-Host "You will be prompted for password..." -ForegroundColor Yellow
}

Write-Host ""

# Upload files
$successCount = 0
$failCount = 0

foreach ($file in $filesToUpload) {
    Write-Host "Uploading: $file" -ForegroundColor Cyan -NoNewline
    $target = "$serverAddr`:$ServerPath/"
    
    $scpCmd = @($scpArgs + $file + $target)
    & scp @scpCmd 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host " - OK" -ForegroundColor Green
        $successCount++
    } else {
        Write-Host " - FAILED" -ForegroundColor Red
        $failCount++
    }
}

# Upload login.html if exists
if (Test-Path "login.html") {
    Write-Host "Uploading: login.html" -ForegroundColor Cyan -NoNewline
    $target = "$serverAddr`:$ServerPath/"
    $scpCmd = @($scpArgs + "login.html" + $target)
    & scp @scpCmd 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host " - OK" -ForegroundColor Green
        $successCount++
    } else {
        Write-Host " - FAILED" -ForegroundColor Red
        $failCount++
    }
}

# Upload img directory if exists
if (Test-Path "img") {
    Write-Host "Uploading: img/ (directory)" -ForegroundColor Cyan -NoNewline
    $target = "$serverAddr`:$ServerPath/"
    $scpCmd = @($scpArgs + "-r" + "img" + $target)
    & scp @scpCmd 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host " - OK" -ForegroundColor Green
        $successCount++
    } else {
        Write-Host " - FAILED" -ForegroundColor Red
        $failCount++
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  UPLOAD SUMMARY" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Success: $successCount" -ForegroundColor Green
if ($failCount -gt 0) {
    Write-Host "Failed: $failCount" -ForegroundColor Red
}
Write-Host ""

if ($failCount -eq 0) {
    Write-Host "All files uploaded successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next step: Deploy the code on server:" -ForegroundColor Yellow
    Write-Host "  ssh $serverAddr" -ForegroundColor Cyan
    Write-Host "  cd $ServerPath" -ForegroundColor Cyan
    Write-Host "  bash deploy-zero-downtime.sh" -ForegroundColor Cyan
} else {
    Write-Host "Some files failed to upload. Please check your connection." -ForegroundColor Red
}

