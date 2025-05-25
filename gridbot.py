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

# GridBot-Logik mit Preisabfrage und Beispiel-Scan
symbol = "DOGEUSDT"
category = "spot"

try:
    response = session.get_tickers(category=category, symbol=symbol)
    price = float(response["result"]["list"][0]["lastPrice"])
    send_telegram_message(f"✅ GridBot gestartet. Aktueller Preis von {symbol}: {price} USDT")

    # Beispiel: Preisbereich für Grid festlegen
    grid_count = 10
    grid_spacing = 0.5 / 100  # 0.5 % Abstand
    grid_prices = [round(price * (1 + grid_spacing) ** i, 4) for i in range(-grid_count//2, grid_count//2 + 1)]

    send_telegram_message(f"✅ Grid-Preise: {grid_prices}")

except Exception as e:
    send_telegram_message(f"❌ Fehler beim Preisabruf: {str(e)}")
    print("Fehler beim Preisabruf:", e)

# Pause bis zur nächsten Ausführung
send_telegram_message("✅ Grid-Scan abgeschlossen. Bot pausiert für 60 Minuten.")
time.sleep(3600)
