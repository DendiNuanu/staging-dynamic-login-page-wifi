# 🚀 START HERE - First Time Setup

## Step 1: Open PowerShell

1. Press `Windows Key + X`
2. Click **"Windows PowerShell"** or **"Terminal"**
3. Navigate to your project folder:
   ```powershell
   cd D:\SERVER-DO\welcome-to-nuanu-login-page-wifi
   ```

## Step 2: Check if SCP is Available (Quick Test)

Run this command to check:
```powershell
scp
```

**If you see help text** → ✅ You're ready! Go to Step 3.

**If you see "command not found"** → Install OpenSSH:
```powershell
# Run PowerShell as Administrator, then:
Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
```

## Step 3: Test SSH Connection (Optional but Recommended)

Test if you can connect to your server:
```powershell
ssh root@146.190.90.47
```

- **If it asks for password** → Type your server password, then type `exit` to close
- **If it connects without password** → Great! You have SSH key setup
- **If it fails** → Make sure your server is running and accessible

## Step 4: Run the Deployment Script! 🎯

### OPTION A: Quick Deploy (Recommended - Easiest)
```powershell
.\QUICK_DEPLOY.ps1
```

### OPTION B: Upload and Auto-Deploy
```powershell
.\deploy-to-server.ps1 -RunDeploy
```

### OPTION C: Upload Only (then deploy manually later)
```powershell
.\deploy-to-server.ps1
```

---

## ⚡ FASTEST WAY (Copy & Paste This):

```powershell
cd D:\SERVER-DO\welcome-to-nuanu-login-page-wifi
.\QUICK_DEPLOY.ps1
```

That's it! The script will:
1. ✅ Upload all your files
2. ✅ Create a backup on server
3. ✅ Set permissions
4. ⚠️ Ask if you want to deploy (say "y" if you want it to run the deployment script)

---

## 🔧 If You Get Errors:

### Error: "Cannot run scripts"
Run this first:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Error: "Permission denied" or "Connection refused"
- Make sure your server is running
- Check if you're using the correct password
- Verify IP address: `146.190.90.47`

### Error: "SCP not found"
Install OpenSSH (see Step 2 above)

---

## ✅ Success Looks Like:

You should see:
```
✅ SCP found: C:\Windows\System32\OpenSSH\scp.exe
✅ SSH connection successful!
📤 Uploading files to server...
  ✅ app.py uploaded
  ✅ requirements.txt uploaded
  ...
✅ Successfully uploaded X items
```

---

## 🎉 After Upload:

If you used `-RunDeploy` or answered "y" to deploy, your code is already live!

If not, SSH to your server and run:
```bash
ssh root@146.190.90.47
cd /var/www/saveemail
bash deploy-zero-downtime.sh
```

---

**That's it! Start with Step 1 and follow the steps above.** 🚀

