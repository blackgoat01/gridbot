import os
import time
import math
import requests
from pybit import HTTP

# === Telegram Funktion ===
def send_telegram(msg):
    try:
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": msg}
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram Fehler:", e)

# === Bybit Session ===
api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
session = HTTP(api_key=api_key, api_secret=api_secret)

symbol = "DOGEUSDT"
budget = 10  # USDT
grid_count = 10
grid_percent = 1  # % Abstand pro Grid

try:
    price = float(session.get_orderbook(symbol=symbol)["result"]["a"][0][0])
except Exception as e:
    send_telegram(f"⚠️ Fehler beim Preisabruf: {str(e)}")
    raise SystemExit

# === Grid-Berechnung ===
low_price = price * (1 - (grid_percent / 100) * grid_count / 2)
high_price = price * (1 + (grid_percent / 100) * grid_count / 2)
grid_spacing = (high_price - low_price) / grid_count
usdt_per_order = budget / grid_count

orders = []
for i in range(grid_count):
    grid_price = round(low_price + grid_spacing * i, 6)
    qty = round(usdt_per_order / grid_price, 2)
    orders.append({"price": grid_price, "qty": qty})

# === Orders platzieren ===
placed = 0
for order in orders:
    try:
        session.place_active_order(
            symbol=symbol,
            side="Buy",
            order_type="Limit",
            qty=order["qty"],
            price=order["price"],
            time_in_force="GoodTillCancel",
            reduce_only=False
        )
        placed += 1
        time.sleep(0.3)
    except Exception as e:
        send_telegram(f"⚠️ Orderfehler bei {order['price']}: {str(e)}")

send_telegram(f"✅ GridBot aktiv auf {symbol}: {placed}/{grid_count} Buy-Orders platziert bei Preis ~ {price:.05f} USDT")
