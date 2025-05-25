import os
import time
import requests
from pybit.unified_trading import HTTP

# Telegram-Benachrichtigung
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": message}
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram Fehler:", e)

# Bybit-Verbindung
session = HTTP(
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET"),
    testnet=False
)

send_telegram_message("✅ GridBot wurde gestartet und ist aktiv.")

symbol = "DOGEUSDT"
interval = 60 * 60  # 60 Minuten

try:
    ticker = session.get_ticker(category="spot", symbol=symbol)
    price = float(ticker["result"]["lastPrice"])
except Exception as e:
    send_telegram_message(f"⚠️ Fehler beim Preisabruf: {str(e)}")
    price = None

if price:
    grids = 10
    spread = 0.01  # 1% pro Grid
    quantity = 10  # Beispielmenge

    lower = price * (1 - (spread * grids / 2))
    upper = price * (1 + (spread * grids / 2))
    step = (upper - lower) / grids

    grid_prices = [round(lower + i * step, 4) for i in range(grids + 1)]

    send_telegram_message("📊 Grid-Scan abgeschlossen. Warte 60 min.")
else:
    send_telegram_message("❌ Grid-Scan konnte nicht durchgeführt werden.")

time.sleep(interval)
