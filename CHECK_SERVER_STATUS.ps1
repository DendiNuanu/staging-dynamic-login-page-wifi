# Check server connection status
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CHECKING SERVER CONNECTION" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$server = "146.190.90.47"

# Test 1: Ping
Write-Host "1. Testing ping..." -ForegroundColor Yellow
$ping = Test-Connection -ComputerName $server -Count 4 -Quiet
if ($ping) {
    Write-Host "   OK - Server is reachable" -ForegroundColor Green
} else {
    Write-Host "   FAILED - Server is not reachable" -ForegroundColor Red
}

Write-Host ""

# Test 2: Port 22 (SSH)
Write-Host "2. Testing SSH port (22)..." -ForegroundColor Yellow
$port = Test-NetConnection -ComputerName $server -Port 22 -WarningAction SilentlyContinue
if ($port.TcpTestSucceeded) {
    Write-Host "   OK - Port 22 is open" -ForegroundColor Green
} else {
    Write-Host "   FAILED - Port 22 is closed or filtered" -ForegroundColor Red
}

Write-Host ""

# Test 3: SSH Connection (verbose)
Write-Host "3. Testing SSH connection..." -ForegroundColor Yellow
Write-Host "   (This will show detailed connection info)" -ForegroundColor Gray
Write-Host ""

$sshTest = ssh -v root@$server "echo 'Connection successful'" 2>&1 | Select-Object -First 20
$sshTest | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DIAGNOSIS COMPLETE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "If connection is closed:" -ForegroundColor Yellow
Write-Host "  1. Wait 10-15 minutes (IP might be blocked)" -ForegroundColor White
Write-Host "  2. Check DigitalOcean dashboard" -ForegroundColor White
Write-Host "  3. Try using web console to access server" -ForegroundColor White
Write-Host ""

