import os
import time
import requests
from pybit.unified_trading import HTTP

# Telegram-Funktion
def send_telegram(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(url, data={"chat_id": chat_id, "text": message})
    except Exception as e:
        print("Telegram-Fehler:", e)

# Bybit API-Verbindung
session = HTTP(
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET")
)

symbol = "DOGEUSDT"
category = "spot"
usdt_per_order = 10
profit_margin = 0.01  # 1% Gewinnziel
check_interval = 15 * 60  # alle 15 Minuten

def get_price():
    response = session.get_tickers(category=category, symbol=symbol)
    return float(response["result"]["list"][0]["lastPrice"])

def check_order_filled(order_id):
    try:
        order = session.get_order_list(category=category, symbol=symbol, orderId=order_id)
        return order["result"]["list"][0]["orderStatus"] == "Filled"
    except Exception as e:
        send_telegram(f"❌ Fehler bei Statusprüfung: {str(e)}")
        return False

while True:
    try:
        price = get_price()
        send_telegram(f"✅ GridBot läuft (15 Min). {symbol} = {price} USDT")

        # Kaufpreis berechnen
        qty = round(usdt_per_order / price, 1)  # 1 Dezimalstelle für DOGE
        buy_price = round(price * 0.995, 4)
        sell_price = round(buy_price * (1 + profit_margin), 4)

        # Kauforder
        order = session.place_order(
            category=category,
            symbol=symbol,
            side="Buy",
            order_type="Limit",
            qty=qty,
            price=buy_price,
            time_in_force="GTC"
        )
        order_id = order["result"]["orderId"]
        send_telegram(f"📥 Limit-Buy platziert: {qty} DOGE @ {buy_price} USDT")

        # Warten auf Ausführung
        for _ in range(60):
            time.sleep(15)
            if check_order_filled(order_id):
                send_telegram(f"✅ Buy Order ausgeführt: {qty} DOGE @ {buy_price}")
                break
        else:
            send_telegram("⏳ Buy-Order nicht ausgeführt – keine Sell-Order platziert.")
            continue

        # Verkaufsorder
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
        send_telegram(f"❌ Fehler: {str(e)}")

    time.sleep(check_interval)
