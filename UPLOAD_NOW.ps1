# Upload all files at once with password
$password = "Fujimori6Riho"
$server = "root@146.190.90.47"
$path = "/var/www/wifi_hotspot"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  UPLOADING ALL FILES TO SERVER" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Create a temporary script file for password
$passFile = "$env:TEMP\sshpass_$(Get-Random).txt"
$password | Out-File -FilePath $passFile -Encoding ASCII -NoNewline

# Function to upload with password
function Upload-File {
    param($file, $isDir = $false)
    
    if (-not (Test-Path $file)) {
        Write-Host "Skipping $file (not found)" -ForegroundColor Yellow
        return $false
    }
    
    Write-Host "Uploading: $file" -ForegroundColor Cyan
    
    if ($isDir) {
        $cmd = "scp -r `"$file`" ${server}:${path}/"
    } else {
        $cmd = "scp `"$file`" ${server}:${path}/"
    }
    
    # Use sshpass equivalent - try multiple methods
    $result = $false
    
    # Method 1: Try using plink if available
    if (Get-Command plink -ErrorAction SilentlyContinue) {
        if ($isDir) {
            & plink -pw $password -batch $server "mkdir -p ${path}/$(Split-Path $file -Leaf)" 2>$null
            & pscp -pw $password -r $file "${server}:${path}/" 2>&1 | Out-Null
        } else {
            & pscp -pw $password $file "${server}:${path}/" 2>&1 | Out-Null
        }
        if ($LASTEXITCODE -eq 0) { $result = $true }
    }
    
    # Method 2: Use expect-like approach with PowerShell
    if (-not $result) {
        $process = Start-Process -FilePath "scp" -ArgumentList @(if($isDir){"-r"}, $file, "${server}:${path}/") -NoNewWindow -PassThru -RedirectStandardError "$env:TEMP\scp_error.log"
        
        # Send password
        $process.StandardInput.WriteLine($password)
        $process.StandardInput.Close()
        
        $process.WaitForExit(30000)
        if ($process.ExitCode -eq 0) { $result = $true }
    }
    
    # Method 3: Direct SCP with password in command (using sshpass equivalent)
    if (-not $result) {
        # Try using echo to pipe password
        $passCmd = "echo $password | scp"
        if ($isDir) {
            $fullCmd = "$passCmd -r `"$file`" ${server}:${path}/"
        } else {
            $fullCmd = "$passCmd `"$file`" ${server}:${path}/"
        }
        
        # Use cmd to execute
        $output = cmd /c "echo $password | scp $(if($isDir){'-r'}) `"$file`" ${server}:${path}/" 2>&1
        if ($LASTEXITCODE -eq 0) { $result = $true }
    }
    
    if ($result) {
        Write-Host "  OK" -ForegroundColor Green
        return $true
    } else {
        Write-Host "  FAILED - Trying manual method..." -ForegroundColor Red
        return $false
    }
}

# Upload all files
$files = @("app.py", "requirements.txt", "gunicorn_config.py", "monitor.py", "deploy-zero-downtime.sh", "deploy.sh", "login.html")
$success = 0
$failed = 0

foreach ($file in $files) {
    if (Upload-File $file) {
        $success++
    } else {
        $failed++
    }
}

# Upload img directory
if (Test-Path "img") {
    if (Upload-File "img" -isDir $true) {
        $success++
    } else {
        $failed++
    }
}

# Cleanup
Remove-Item $passFile -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  UPLOAD COMPLETE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Success: $success" -ForegroundColor Green
if ($failed -gt 0) {
    Write-Host "Failed: $failed" -ForegroundColor Red
}

