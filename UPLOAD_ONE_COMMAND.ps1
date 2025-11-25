# ONE COMMAND TO UPLOAD ALL FILES
$pass = "Fujimori6Riho"
$server = "root@146.190.90.47"
$path = "/var/www/wifi_hotspot"

Write-Host "UPLOADING ALL FILES..." -ForegroundColor Green

# Use expect-like method with PowerShell
function Upload-WithPassword {
    param($file, $isDir = $false)
    
    if (-not (Test-Path $file)) { return }
    
    Write-Host "Uploading: $file" -ForegroundColor Cyan
    
    $scpArgs = @()
    if ($isDir) { $scpArgs += "-r" }
    $scpArgs += $file
    $scpArgs += "${server}:${path}/"
    
    # Create expect script
    $expectScript = @"
spawn scp $($scpArgs -join ' ')
expect "password:"
send "$pass\r"
expect eof
"@
    
    # Try using plink/pscp if available
    if (Get-Command pscp -ErrorAction SilentlyContinue) {
        if ($isDir) {
            & pscp -pw $pass -r $file "${server}:${path}/" 2>&1 | Out-Null
        } else {
            & pscp -pw $pass $file "${server}:${path}/" 2>&1 | Out-Null
        }
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  OK" -ForegroundColor Green
            return $true
        }
    }
    
    # Fallback: Use cmd with password
    $cmd = "echo $pass | scp $(if($isDir){'-r'}) `"$file`" ${server}:${path}/"
    $result = cmd /c $cmd 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  OK" -ForegroundColor Green
        return $true
    }
    
    Write-Host "  FAILED" -ForegroundColor Red
    return $false
}

# Upload all files
$files = @("app.py", "requirements.txt", "gunicorn_config.py", "monitor.py", "deploy-zero-downtime.sh", "deploy.sh", "login.html")
foreach ($f in $files) { Upload-WithPassword $f }
if (Test-Path "img") { Upload-WithPassword "img" -isDir $true }

Write-Host "`nUPLOAD COMPLETE!" -ForegroundColor Green

