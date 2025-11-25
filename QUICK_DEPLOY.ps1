# ============================================
# QUICK DEPLOY - Easy one-command deployment
# ============================================

# Load configuration if it exists
if (Test-Path "deploy-config.ps1") {
    . .\deploy-config.ps1
    Write-Host "✅ Loaded configuration from deploy-config.ps1" -ForegroundColor Green
} else {
    Write-Host "⚠️  No deploy-config.ps1 found, using defaults" -ForegroundColor Yellow
}

# Run the deployment script with loaded config
$params = @{
    ServerIP = $script:ServerIP
    ServerUser = $script:ServerUser
    ServerPath = $script:ServerPath
    RunDeploy = $script:AutoDeploy
    SkipBackup = $script:SkipBackup
}

if ($script:SSHKey) {
    $params.SSHKey = $script:SSHKey
}

& .\deploy-to-server.ps1 @params

