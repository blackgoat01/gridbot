import os
import time
from pybit.unified_trading import HTTP
import requests

# Telegram-Konfiguration
def send_telegram_message(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram-Fehler:", e)

# Bybit-Verbindung
session = HTTP(
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET")
)

# GridBot-Logik mit Preisabfrage und Schutz vor doppelten Orders
symbol = "DOGEUSDT"
category = "spot"
last_price = None

while True:
    try:
        response = session.get_tickers(category=category, symbol=symbol)
        price = float(response["result"]["list"][0]["lastPrice"])

        if price != last_price:
            last_price = price
            send_telegram_message(f"✅ GridBot läuft (15 Min). DOGEUSDT = {price} USDT")

            # Grid-Level-Berechnung
            grid_count = 10
            grid_spacing = 0.005  # 0.5 %
            grid_prices = [round(price * (1 + grid_spacing) ** i, 4) for i in range(-grid_count//2, grid_count//2 + 1)]

            send_telegram_message(f"📊 Grid-Level: {grid_prices}")
        else:
            send_telegram_message("🔁 Kein Preiswechsel – keine neue Order notwendig.")

    except Exception as e:
        send_telegram_message(f"❌ Fehler beim Abrufen: {str(e)}")

    time.sleep(900)  # 15 Minuten
