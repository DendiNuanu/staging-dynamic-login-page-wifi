$pass = "Fujimori6Riho"
$server = "root@146.190.90.47"
$path = "/var/www/wifi_hotspot"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  UPLOADING ALL FILES AT ONCE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Check if sshpass exists, if not download it
if (-not (Test-Path "sshpass.exe")) {
    Write-Host "Downloading sshpass..." -ForegroundColor Yellow
    try {
        Invoke-WebRequest -Uri "https://github.com/keimpx/sshpass-windows/releases/download/v1.06/sshpass.exe" -OutFile "sshpass.exe" -UseBasicParsing
        Write-Host "sshpass downloaded!" -ForegroundColor Green
    } catch {
        Write-Host "Failed to download sshpass. Using manual method..." -ForegroundColor Red
    }
}

$files = @("app.py", "requirements.txt", "gunicorn_config.py", "monitor.py", "deploy-zero-downtime.sh", "deploy.sh", "login.html")
$success = 0

if (Test-Path "sshpass.exe") {
    Write-Host "Using sshpass for password authentication..." -ForegroundColor Cyan
    Write-Host ""
    
    foreach ($file in $files) {
        if (Test-Path $file) {
            Write-Host "Uploading: $file" -ForegroundColor Cyan -NoNewline
            $target = "$server`:$path/"
            & .\sshpass.exe -p $pass scp $file $target 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Host " - OK" -ForegroundColor Green
                $success++
            } else {
                Write-Host " - FAILED" -ForegroundColor Red
            }
        }
    }
    
    if (Test-Path "img") {
        Write-Host "Uploading: img/" -ForegroundColor Cyan -NoNewline
        $target = "$server`:$path/"
        & .\sshpass.exe -p $pass scp -r img $target 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host " - OK" -ForegroundColor Green
            $success++
        } else {
            Write-Host " - FAILED" -ForegroundColor Red
        }
    }
} else {
    Write-Host "sshpass not available. Please run files manually or install sshpass." -ForegroundColor Red
    Write-Host ""
    Write-Host "Manual upload commands:" -ForegroundColor Yellow
    foreach ($file in $files) {
        if (Test-Path $file) {
            Write-Host "scp $file $server`:$path/" -ForegroundColor Cyan
        }
    }
    if (Test-Path "img") {
        Write-Host "scp -r img $server`:$path/" -ForegroundColor Cyan
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  UPLOAD COMPLETE - $success files uploaded" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

