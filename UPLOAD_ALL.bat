@echo off
echo ========================================
echo   UPLOADING ALL FILES TO SERVER
echo ========================================
echo.
echo Server: root@146.190.90.47
echo Path: /var/www/wifi_hotspot
echo.
echo You will be prompted for password multiple times.
echo Enter your server password when asked.
echo.
pause

echo.
echo Uploading app.py...
scp app.py root@146.190.90.47:/var/www/wifi_hotspot/
if %errorlevel% neq 0 (
    echo ERROR: Failed to upload app.py
    pause
    exit /b 1
)

echo Uploading requirements.txt...
scp requirements.txt root@146.190.90.47:/var/www/wifi_hotspot/
if %errorlevel% neq 0 (
    echo ERROR: Failed to upload requirements.txt
    pause
    exit /b 1
)

echo Uploading gunicorn_config.py...
scp gunicorn_config.py root@146.190.90.47:/var/www/wifi_hotspot/
if %errorlevel% neq 0 (
    echo ERROR: Failed to upload gunicorn_config.py
    pause
    exit /b 1
)

echo Uploading monitor.py...
scp monitor.py root@146.190.90.47:/var/www/wifi_hotspot/
if %errorlevel% neq 0 (
    echo ERROR: Failed to upload monitor.py
    pause
    exit /b 1
)

echo Uploading deploy-zero-downtime.sh...
scp deploy-zero-downtime.sh root@146.190.90.47:/var/www/wifi_hotspot/
if %errorlevel% neq 0 (
    echo ERROR: Failed to upload deploy-zero-downtime.sh
    pause
    exit /b 1
)

echo Uploading deploy.sh...
scp deploy.sh root@146.190.90.47:/var/www/wifi_hotspot/
if %errorlevel% neq 0 (
    echo ERROR: Failed to upload deploy.sh
    pause
    exit /b 1
)

if exist login.html (
    echo Uploading login.html...
    scp login.html root@146.190.90.47:/var/www/wifi_hotspot/
    if %errorlevel% neq 0 (
        echo ERROR: Failed to upload login.html
        pause
        exit /b 1
    )
)

if exist img (
    echo Uploading img directory...
    scp -r img root@146.190.90.47:/var/www/wifi_hotspot/
    if %errorlevel% neq 0 (
        echo ERROR: Failed to upload img directory
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo   UPLOAD COMPLETED SUCCESSFULLY!
echo ========================================
echo.
echo Next step: Deploy the code
echo   ssh root@146.190.90.47
echo   cd /var/www/wifi_hotspot
echo   bash deploy-zero-downtime.sh
echo.
pause

