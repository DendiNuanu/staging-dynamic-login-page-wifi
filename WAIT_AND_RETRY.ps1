# Wait and retry SSH connection
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "  WAITING 15 MINUTES FOR IP UNBLOCK" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "Your IP was likely blocked due to failed login attempts." -ForegroundColor Red
Write-Host "Waiting 15 minutes for the block to clear..." -ForegroundColor Yellow
Write-Host ""

$minutes = 15
$seconds = $minutes * 60

for ($i = $seconds; $i -gt 0; $i--) {
    $mins = [math]::Floor($i / 60)
    $secs = $i % 60
    Write-Host "`rWaiting: $mins min $secs sec remaining..." -NoNewline -ForegroundColor Cyan
    Start-Sleep -Seconds 1
}

Write-Host ""
Write-Host ""
Write-Host "Time's up! Trying connection now..." -ForegroundColor Green
Write-Host ""

# Test connection
ssh root@146.190.90.47

