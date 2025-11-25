@echo off
echo ========================================
echo   UPLOAD ALL FILES - ONE BY ONE
echo ========================================
echo.
echo Password: Fujimori6Riho
echo You will enter password 8 times (once per file)
echo.
pause

scp app.py root@146.190.90.47:/var/www/wifi_hotspot/
scp requirements.txt root@146.190.90.47:/var/www/wifi_hotspot/
scp gunicorn_config.py root@146.190.90.47:/var/www/wifi_hotspot/
scp monitor.py root@146.190.90.47:/var/www/wifi_hotspot/
scp deploy-zero-downtime.sh root@146.190.90.47:/var/www/wifi_hotspot/
scp deploy.sh root@146.190.90.47:/var/www/wifi_hotspot/
scp login.html root@146.190.90.47:/var/www/wifi_hotspot/
scp -r img root@146.190.90.47:/var/www/wifi_hotspot/

echo.
echo ========================================
echo   UPLOAD COMPLETE!
echo ========================================
pause

