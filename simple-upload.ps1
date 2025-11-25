# Simple upload script
param(
    [string]$ServerIP = "146.190.90.47",
    [string]$ServerUser = "root",
    [string]$ServerPath = "/var/www/wifi_hotspot"
)

$serverAddr = $ServerUser + "@" + $ServerIP

$uploadTarget = "$serverAddr`:$ServerPath"
Write-Host "Uploading files to $uploadTarget" -ForegroundColor Green

# Files to upload
$files = @("app.py", "requirements.txt", "gunicorn_config.py", "monitor.py", "deploy-zero-downtime.sh", "deploy.sh", "login.html")

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "Uploading: $file" -ForegroundColor Cyan
        $target = "$serverAddr`:$ServerPath/"
        scp $file $target
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  OK" -ForegroundColor Green
        } else {
            Write-Host "  FAILED" -ForegroundColor Red
        }
    }
}

# Upload img directory
if (Test-Path "img") {
    Write-Host "Uploading: img/" -ForegroundColor Cyan
    $target = "$serverAddr`:$ServerPath/"
    scp -r img $target
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  OK" -ForegroundColor Green
    } else {
        Write-Host "  FAILED" -ForegroundColor Red
    }
}

Write-Host "`nUpload completed!" -ForegroundColor Green

