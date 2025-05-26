import os
import time
from pybit.unified_trading import HTTP
import requests

# Telegram-Benachrichtigung
def send_telegram(message):
    try:
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": message})
    except Exception as e:
        print("Telegram Fehler:", e)

# Bybit-Verbindung
session = HTTP(
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET")
)

symbol = "DOGEUSDT"
category = "spot"
usdt_per_order = 10
profit_margin = 0.01  # 1% Ziel
grid_spacing = 0.005  # 0.5%
grid_count = 10
last_price = None

def round_qty(qty):
    return round(qty, 0)  # Nur ganze DOGE-Mengen

def order_exists(side, price):
    try:
        orders = session.get_open_orders(category=category, symbol=symbol)["result"]["list"]
        for order in orders:
            if order["side"].lower() == side.lower() and abs(float(order["price"]) - price) < 0.0001:
                return True
    except Exception as e:
        send_telegram(f"⚠️ Fehler bei Orderprüfung: {str(e)}")
    return False

while True:
    try:
        price_data = session.get_tickers(category=category, symbol=symbol)
        price = float(price_data["result"]["list"][0]["lastPrice"])
        send_telegram(f"✅ GridBot läuft (15 Min). {symbol} = {price} USDT")

        grid_prices = [round(price * (1 + grid_spacing) ** i, 4)
                       for i in range(-grid_count // 2, grid_count // 2 + 1)]
        buy_price = min(grid_prices)
        qty = round_qty(usdt_per_order / buy_price)

        if not order_exists("Buy", buy_price):
            try:
                session.place_order(
                    category=category,
                    symbol=symbol,
                    side="Buy",
                    order_type="Limit",
                    qty=qty,
                    price=buy_price,
                    time_in_force="GTC"
                )
                send_telegram(f"📥 Limit-Buy platziert: {qty} DOGE @ {buy_price} USDT")
            except Exception as e:
                send_telegram(f"⚠️ Fehler bei Kauforder: {str(e)}")

        sell_price = round(buy_price * (1 + profit_margin), 4)
        if not order_exists("Sell", sell_price):
            try:
                session.place_order(
                    category=category,
                    symbol=symbol,
                    side="Sell",
                    order_type="Limit",
                    qty=qty,
                    price=sell_price,
                    time_in_force="GTC"
                )
                send_telegram(f"📤 Limit-Sell platziert: {qty} DOGE @ {sell_price} USDT")
            except Exception as e:
                send_telegram(f"⚠️ Fehler bei Sellorder: {str(e)}")

    except Exception as e:
        send_telegram(f"❌ API-Verbindungsfehler: {str(e)}")

    time.sleep(900)  # 15 Minuten
