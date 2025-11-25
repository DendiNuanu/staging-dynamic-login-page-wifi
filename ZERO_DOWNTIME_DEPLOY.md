# 🚀 Zero-Downtime Deployment Guide

## Quick Start

### Option 1: Use the Enhanced Zero-Downtime Script (RECOMMENDED)
```bash
chmod +x deploy-zero-downtime.sh
./deploy-zero-downtime.sh
```

### Option 2: Use the Updated Regular Deploy Script
```bash
chmod +x deploy.sh
./deploy.sh
```

## What Changed?

### ✅ Zero-Downtime Features Added:

1. **Graceful Reload** - Uses `systemctl reload` instead of `restart`
   - Sends HUP signal to Gunicorn master process
   - Workers reload one-by-one without stopping service
   - **NO DOWNTIME!**

2. **Health Checks** - Verifies service before and after deployment
   - Pre-deployment check ensures service is running
   - Post-deployment check verifies new code works
   - Automatic rollback if health check fails

3. **Automatic Backups** - Creates backup before deploying
   - Saves current code to `/var/www/saveemail/backups/`
   - Keeps last 5 backups automatically
   - Easy rollback if something goes wrong

4. **Smart Error Handling** - Automatic rollback on failure
   - If deployment fails, automatically restores previous version
   - Sends Telegram notifications for all events

## How It Works

### Traditional Deployment (WITH DOWNTIME):
```
1. Stop old server ❌ (downtime starts)
2. Install new code
3. Start new server ✅ (downtime ends)
```

### Zero-Downtime Deployment (NO DOWNTIME):
```
1. Install new code (old server still running) ✅
2. Send HUP signal to Gunicorn
3. Gunicorn spawns new workers with new code
4. New workers handle new requests
5. Old workers finish current requests and die
6. Service never stops! ✅
```

## Setup Instructions

### 1. Make Scripts Executable
```bash
chmod +x deploy-zero-downtime.sh
chmod +x deploy.sh
```

### 2. Ensure Gunicorn Service Supports Reload

Check your systemd service file (`/etc/systemd/system/gunicorn.service`):

```ini
[Service]
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
```

If it doesn't have `ExecReload`, update it:
```bash
sudo nano /etc/systemd/system/gunicorn.service
# Add: ExecReload=/bin/kill -s HUP $MAINPID
sudo systemctl daemon-reload
```

### 3. (Optional) Use Gunicorn Config File

For better control, use the provided `gunicorn_config.py`:

1. Update your systemd service to use the config:
```ini
ExecStart=/var/www/saveemail/venv/bin/gunicorn \
          --config /var/www/saveemail/gunicorn_config.py \
          app:app
```

2. Reload systemd:
```bash
sudo systemctl daemon-reload
sudo systemctl restart gunicorn
```

## Deployment Process

### Step-by-Step What Happens:

1. **Pre-flight Checks**
   - Health check on current service
   - Verify service is running

2. **Backup Current Code**
   - Creates timestamped backup
   - Saves to `/var/www/saveemail/backups/`

3. **Install Dependencies**
   - Updates Python packages
   - Safe to do while service is running

4. **Test Configuration**
   - Validates Nginx config
   - Aborts if invalid

5. **Graceful Reload** ⭐ (ZERO-DOWNTIME)
   - Sends HUP signal to Gunicorn
   - New workers start with new code
   - Old workers finish and die gracefully
   - **Service never stops!**

6. **Reload Nginx**
   - Graceful reload (no downtime)

7. **Post-deployment Health Check**
   - Verifies new code is working
   - Automatic rollback if failed

8. **Cleanup**
   - Removes old backups (keeps last 5)

## Rollback Procedure

### Automatic Rollback
If deployment fails, the script automatically:
1. Detects failure
2. Restores from backup
3. Reloads service
4. Sends notification

### Manual Rollback
If you need to rollback manually:

```bash
cd /var/www/saveemail/backups
ls -lt  # Find latest backup
cd backup_YYYYMMDD_HHMMSS  # Use latest backup
cp -r * /var/www/saveemail/
sudo systemctl reload gunicorn
```

## Monitoring

### Check Service Status
```bash
sudo systemctl status gunicorn
sudo systemctl status nginx
```

### Check Logs
```bash
# Gunicorn logs
sudo journalctl -u gunicorn -f

# Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

### Health Check Manually
```bash
curl -I https://wifi.nuanu.io/api/settings
# Should return: HTTP/2 200
```

## Troubleshooting

### Issue: "Gunicorn process not found"
**Solution**: Service might not be running. Start it first:
```bash
sudo systemctl start gunicorn
```

### Issue: "Health check failed"
**Solution**: Check if service is actually running:
```bash
sudo systemctl status gunicorn
curl https://wifi.nuanu.io/api/settings
```

### Issue: "Permission denied"
**Solution**: Make sure script is executable:
```bash
chmod +x deploy-zero-downtime.sh
```

### Issue: Service still has downtime
**Solution**: Check if systemd service has `ExecReload`:
```bash
cat /etc/systemd/system/gunicorn.service | grep ExecReload
# Should show: ExecReload=/bin/kill -s HUP $MAINPID
```

## Best Practices

1. **Always test locally first** before deploying
2. **Deploy during low-traffic periods** (even though it's zero-downtime)
3. **Monitor logs** after deployment
4. **Keep backups** (script does this automatically)
5. **Use health checks** (script does this automatically)

## Comparison

| Feature | Old deploy.sh | New deploy.sh | deploy-zero-downtime.sh |
|---------|---------------|---------------|-------------------------|
| Downtime | ❌ Yes | ✅ No | ✅ No |
| Health Checks | ❌ No | ❌ No | ✅ Yes |
| Auto Backup | ❌ No | ❌ No | ✅ Yes |
| Auto Rollback | ❌ No | ❌ No | ✅ Yes |
| Notifications | ✅ Yes | ✅ Yes | ✅ Yes |

## Quick Reference

```bash
# Zero-downtime deployment (RECOMMENDED)
./deploy-zero-downtime.sh

# Regular deployment (also zero-downtime now)
./deploy.sh

# Check service status
sudo systemctl status gunicorn

# View logs
sudo journalctl -u gunicorn -f

# Manual reload (zero-downtime)
sudo systemctl reload gunicorn

# Manual restart (WITH downtime)
sudo systemctl restart gunicorn
```

## 🎉 You're All Set!

Your deployment is now **ZERO-DOWNTIME**! Deploy with confidence! 🚀

