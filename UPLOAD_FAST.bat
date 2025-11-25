@echo off
echo Uploading all files at once...
echo.

REM Create a script that pipes password to SCP
echo Fujimori6Riho| scp app.py root@146.190.90.47:/var/www/wifi_hotspot/
echo Fujimori6Riho| scp requirements.txt root@146.190.90.47:/var/www/wifi_hotspot/
echo Fujimori6Riho| scp gunicorn_config.py root@146.190.90.47:/var/www/wifi_hotspot/
echo Fujimori6Riho| scp monitor.py root@146.190.90.47:/var/www/wifi_hotspot/
echo Fujimori6Riho| scp deploy-zero-downtime.sh root@146.190.90.47:/var/www/wifi_hotspot/
echo Fujimori6Riho| scp deploy.sh root@146.190.90.47:/var/www/wifi_hotspot/
echo Fujimori6Riho| scp login.html root@146.190.90.47:/var/www/wifi_hotspot/
echo Fujimori6Riho| scp -r img root@146.190.90.47:/var/www/wifi_hotspot/

echo.
echo Upload complete!

