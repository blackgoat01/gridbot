import os
import time
import requests
from pybit.unified_trading import HTTP

# Telegram Nachricht senden
def send_telegram_message(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram-Fehler:", e)

# Bybit-Session
session = HTTP(
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET")
)

# Einstieg
send_telegram_message("✅ GridBot wurde gestartet und ist aktiv.")

symbol = "DOGEUSDT"

try:
    # Preis abfragen
    ticker_data = session.get_tickers(symbol=symbol)
    price = float(ticker_data["result"]["list"][0]["lastPrice"])

    # Orderbuch abfragen
    orderbook_data = session.get_order_book(symbol=symbol)
    best_bid = float(orderbook_data["result"]["b"][0][0])
    best_ask = float(orderbook_data["result"]["a"][0][0])

    send_telegram_message(f"📊 {symbol} Preis: {price} | Bid: {best_bid} | Ask: {best_ask}")

except Exception as e:
    send_telegram_message(f"⚠️ Fehler beim Preisabruf: {str(e)}")

# Wartezeit (nur Testlauf)
time.sleep(10)
send_telegram_message("✅ Grid-Scan abgeschlossen. Bot pausiert 60 Minuten.")
