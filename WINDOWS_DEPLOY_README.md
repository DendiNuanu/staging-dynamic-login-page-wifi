# 🚀 Windows Auto-Upload to DigitalOcean - Quick Guide

## Overview

This guide helps you automatically upload your local code to your DigitalOcean server from Windows 11.

## 📋 Prerequisites

1. **OpenSSH Client** (usually pre-installed on Windows 10/11)
   - Check: Open PowerShell and type `scp`
   - If not found, install: `Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0` (as Administrator)

2. **SSH Access** to your DigitalOcean server
   - Either password authentication OR SSH key
   - Server IP: `146.190.90.47`
   - Default user: `root` (or your configured user)

## 🎯 Quick Start

### Option 1: Quick Deploy (Recommended)

1. **Edit configuration** (optional):
   ```powershell
   # Open deploy-config.ps1 and update if needed
   notepad deploy-config.ps1
   ```

2. **Run the quick deploy script**:
   ```powershell
   .\QUICK_DEPLOY.ps1
   ```

That's it! The script will:
- ✅ Upload all necessary files
- ✅ Create a backup on the server
- ✅ Set proper file permissions
- ✅ Optionally run the deployment script

### Option 2: Manual Deploy

1. **Upload files only**:
   ```powershell
   .\deploy-to-server.ps1
   ```

2. **Upload and auto-deploy**:
   ```powershell
   .\deploy-to-server.ps1 -RunDeploy
   ```

3. **With custom settings**:
   ```powershell
   .\deploy-to-server.ps1 -ServerIP "146.190.90.47" -ServerUser "root" -ServerPath "/var/www/saveemail" -RunDeploy
   ```

## ⚙️ Configuration

Edit `deploy-config.ps1` to customize:

```powershell
$script:ServerIP = "146.190.90.47"      # Your server IP
$script:ServerUser = "root"              # SSH username
$script:ServerPath = "/var/www/saveemail" # Deployment path
$script:SSHKey = ""                      # Path to SSH key (optional)
$script:AutoDeploy = $false              # Auto-run deployment script?
$script:SkipBackup = $false              # Skip backup before upload?
```

## 🔑 Using SSH Key Authentication

1. **Generate SSH key** (if you don't have one):
   ```powershell
   ssh-keygen -t rsa -b 4096
   ```

2. **Copy public key to server**:
   ```powershell
   type $env:USERPROFILE\.ssh\id_rsa.pub | ssh root@146.190.90.47 "cat >> ~/.ssh/authorized_keys"
   ```

3. **Update config**:
   ```powershell
   $script:SSHKey = "$env:USERPROFILE\.ssh\id_rsa"
   ```

## 📤 What Gets Uploaded

The script uploads:
- ✅ `app.py` - Main application
- ✅ `requirements.txt` - Python dependencies
- ✅ `gunicorn_config.py` - Gunicorn configuration
- ✅ `monitor.py` - Monitoring script
- ✅ `deploy-zero-downtime.sh` - Deployment script
- ✅ `deploy.sh` - Alternative deployment script
- ✅ `login.html` - Login page
- ✅ `img/` - Image directory

**Excluded:**
- ❌ `__pycache__/` - Python cache
- ❌ `.env` - Environment file (keep on server)
- ❌ `.git/` - Git repository
- ❌ `*.log` - Log files

## 🔍 Troubleshooting

### "SCP not found"
- Install OpenSSH Client (see Prerequisites)
- Or use WinSCP/PuTTY as alternative

### "Permission denied"
- Check SSH key permissions
- Try password authentication (leave SSHKey empty)
- Verify username is correct

### "Connection timeout"
- Check server IP is correct
- Verify firewall allows SSH (port 22)
- Check if server is running

### "Upload failed"
- Check disk space on server
- Verify deployment path exists
- Check file permissions on server

## 📝 Manual Steps (if script fails)

1. **SSH to server**:
   ```powershell
   ssh root@146.190.90.47
   ```

2. **Navigate to app directory**:
   ```bash
   cd /var/www/saveemail
   ```

3. **Create backup**:
   ```bash
   mkdir -p backups
   tar -czf backups/backup_$(date +%Y%m%d_%H%M%S).tar.gz *.py *.txt *.sh *.html img/
   ```

4. **Upload files manually** (using WinSCP, FileZilla, or SCP):
   ```powershell
   scp app.py root@146.190.90.47:/var/www/saveemail/
   scp requirements.txt root@146.190.90.47:/var/www/saveemail/
   # ... etc
   ```

5. **Run deployment**:
   ```bash
   cd /var/www/saveemail
   bash deploy-zero-downtime.sh
   ```

## ✅ Verification

After deployment, verify:

1. **Check service status**:
   ```bash
   ssh root@146.190.90.47 "systemctl status gunicorn"
   ```

2. **Test API endpoint**:
   ```powershell
   curl https://wifi.nuanu.io/api/settings
   ```

3. **Check logs**:
   ```bash
   ssh root@146.190.90.47 "tail -f /var/log/gunicorn/error.log"
   ```

## 🎉 Success!

If everything works, you should see:
- ✅ Files uploaded successfully
- ✅ Deployment completed
- ✅ Service running
- ✅ Website accessible at https://wifi.nuanu.io

## 📞 Need Help?

- Check `CODE_REVIEW.md` for code status
- Review server logs: `/var/log/gunicorn/error.log`
- Check deployment script output for errors

---

**Happy Deploying! 🚀**

