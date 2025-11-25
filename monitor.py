import requests
import time
import datetime

# === CONFIG ===
URL = "https://wifi.nuanu.io/dashboard"
TELEGRAM_TOKEN = "7137088973:AAGlJOO7OEDweSkUWlvp7mEDUbyIdJ5Xnmw"
CHAT_ID = "5481015560"

def send_telegram(message: str):
    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(api_url, data={"chat_id": CHAT_ID, "text": message})
    except Exception as e:
        print("Failed to send Telegram message:", e)

def check_site():
    try:
        r = requests.get(URL, timeout=15)
        if r.status_code == 200:
            return True
        else:
            return False
    except Exception:
        return False

# === MAIN LOOP ===
last_up_report = 0  # timestamp of last "UP" report

while True:
    is_up = check_site()
    now = int(time.time())

    if is_up:
        print("✅ Website is UP")
        # kirim notif UP tiap 1 jam sekali
        if now - last_up_report >= 3600:
            send_telegram(f"✅ {URL} is UP and running fine ({datetime.datetime.now()})")
            last_up_report = now
    else:
        print("🚨 Website is DOWN!")
        send_telegram(f"🚨 {URL} is DOWN! ({datetime.datetime.now()})")

    time.sleep(60)  # cek setiap 1 menit

