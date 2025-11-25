$pass = "Fujimori6Riho"
$server = "root@146.190.90.47"
$path = "/var/www/wifi_hotspot"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  UPLOADING ALL FILES" -ForegroundColor Green  
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

$files = @("app.py", "requirements.txt", "gunicorn_config.py", "monitor.py", "deploy-zero-downtime.sh", "deploy.sh", "login.html")

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "Uploading: $file" -ForegroundColor Cyan -NoNewline
        $target = "$server`:$path/"
        
        # Use cmd to pipe password
        $cmd = "echo $pass | scp `"$file`" $target"
        $result = cmd /c $cmd 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host " - OK" -ForegroundColor Green
        } else {
            Write-Host " - FAILED" -ForegroundColor Red
        }
    }
}

if (Test-Path "img") {
    Write-Host "Uploading: img/" -ForegroundColor Cyan -NoNewline
    $target = "$server`:$path/"
    $cmd = "echo $pass | scp -r img $target"
    $result = cmd /c $cmd 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host " - OK" -ForegroundColor Green
    } else {
        Write-Host " - FAILED" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "UPLOAD COMPLETE!" -ForegroundColor Green

