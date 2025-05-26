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

# Bybit-Session initialisieren
session = HTTP(
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET")
)

symbol = "DOGEUSDT"
category = "spot"
usdt_per_order = 10
profit_margin = 0.01
min_qty_precision = 0  # DOGE erlaubt nur ganze Stücke

def get_last_price():
    response = session.get_tickers(category=category, symbol=symbol)
    return float(response["result"]["list"][0]["lastPrice"])

def get_active_orders():
    return session.get_open_orders(category=category, symbol=symbol)["result"]["list"]

def cancel_all_orders():
    try:
        session.cancel_all_orders(category=category, symbol=symbol)
    except Exception as e:
        send_telegram_message(f"❌ Fehler beim Löschen offener Orders: {str(e)}")

def place_limit_buy(qty, price):
    try:
        response = session.place_order(
            category=category,
            symbol=symbol,
            side="Buy",
            order_type="Limit",
            qty=qty,
            price=price,
            time_in_force="GTC"
        )
        send_telegram_message(f"📥 Limit-Buy platziert: {qty} DOGE @ {price} USDT")
        return response["result"]["orderId"]
    except Exception as e:
        send_telegram_message(f"⚠️ Fehler bei Kauforder: {str(e)}")
        return None

def place_limit_sell(qty, price):
    try:
        session.place_order(
            category=category,
            symbol=symbol,
            side="Sell",
            order_type="Limit",
            qty=qty,
            price=price,
            time_in_force="GTC"
        )
        send_telegram_message(f"📤 Limit-Sell platziert: {qty} DOGE @ {price} USDT")
    except Exception as e:
        send_telegram_message(f"⚠️ Fehler bei Sellorder: {str(e)}")

while True:
    try:
        price = get_last_price()
        send_telegram_message(f"✅ GridBot läuft (15 Min). {symbol} = {price} USDT")

        # Grid-Level Berechnung
        grid_spacing = 0.005
        grid_prices = [round(price * (1 + grid_spacing) ** i, 4) for i in range(-5, 6)]
        buy_price = min(grid_prices)
        qty = round(usdt_per_order / buy_price)

        # Vorherige Orders löschen
        cancel_all_orders()

        # Buy-Order setzen
        buy_order_id = place_limit_buy(qty, buy_price)

        # Warten auf Ausführung
        time.sleep(60)
        order_status = session.get_order(
            category=category, symbol=symbol, orderId=buy_order_id
        )["result"]

        if order_status["orderStatus"] == "Filled":
            sell_price = round(buy_price * (1 + profit_margin), 4)
            place_limit_sell(qty, sell_price)
        else:
            send_telegram_message("⌛ Buy-Order noch nicht ausgeführt, Sell wird nicht gesetzt.")

    except Exception as e:
        send_telegram_message(f"❌ Allgemeiner Fehler: {str(e)}")

    time.sleep(900)  # 15 Minuten
