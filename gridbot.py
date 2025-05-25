import os
import requests
from pybit import HTTP
from time import sleep

# Telegram Nachricht senden
def send_telegram_message(msg):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = { "chat_id": chat_id, "text": msg }
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram-Fehler:", e)

# Bybit Session
try:
    session = HTTP(
        api_key=os.getenv("API_KEY"),
        api_secret=os.getenv("API_SECRET")
    )
    price = session.ticker_price(symbol="DOGEUSDT")["price"]
except Exception as e:
    send_telegram_message(f"⚠️ Preisabruf fehlgeschlagen: {str(e)}")
    exit()

send_telegram_message("✅ GridBot wurde gestartet und ist aktiv.")

# Beispielhafte Grid-Strategie (vereinfacht)
try:
    price = float(price)
    grid_count = 10
    grid_spacing = 0.01  # 1% Abstand
    base_price = price

    for i in range(grid_count):
        buy_price = round(base_price * (1 - grid_spacing * (i + 1)), 5)
        sell_price = round(base_price * (1 + grid_spacing * (i + 1)), 5)

        # Debug/Test-Ausgabe - hier würden Orders platziert
        send_telegram_message(f"🔹 Grid {i+1}: Kaufe bei {buy_price}, Verkaufe bei {sell_price}")

    send_telegram_message("✅ Grid-Scan abgeschlossen. Warte 60 min.")
    sleep(3600)

except Exception as e:
    send_telegram_message(f"⚠️ Fehler im Grid-Bot: {str(e)}")
