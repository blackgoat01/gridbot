
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

# Bot-Parameter
symbol = "DOGEUSDT"
category = "spot"
usdt_per_order = 10
profit_margin = 0.01  # 1% Gewinnziel pro Trade

# Rundungsfunktion für Menge
def format_qty(qty):
    return round(qty, 0)  # Ganzzahlige DOGE-Menge

while True:
    try:
        response = session.get_tickers(category=category, symbol=symbol)
        price = float(response["result"]["list"][0]["lastPrice"])
        send_telegram_message(f"✅ GridBot läuft (15 Min). {symbol} = {price} USDT")

        # Grid-Berechnung
        grid_count = 10
        grid_spacing = 0.005
        grid_prices = [round(price * (1 + grid_spacing) ** i, 4) for i in range(-grid_count//2, grid_count//2 + 1)]
        buy_price = min(grid_prices)
        qty = format_qty(usdt_per_order / buy_price)

        # Guthaben prüfen
        balances = session.get_wallet_balance(accountType="UNIFIED")["result"]["list"][0]["coin"]
        usdt_balance = next((coin for coin in balances if coin["coin"] == "USDT"), {"availableToTrade": 0})["availableToTrade"]
        doge_balance = next((coin for coin in balances if coin["coin"] == "DOGE"), {"availableToTrade": 0})["availableToTrade"]
        usdt_balance = float(usdt_balance)
        doge_balance = float(doge_balance)

        if usdt_balance >= qty * buy_price:
            session.place_order(
                category=category,
                symbol=symbol,
                side="Buy",
                order_type="Limit",
                qty=qty,
                price=buy_price,
                time_in_force="GTC"
            )
            send_telegram_message(f"📥 Limit-Buy platziert: {qty} DOGE @ {buy_price} USDT")
        else:
            send_telegram_message(f"⚠️ Nicht genug USDT für Kauf ({qty} DOGE @ {buy_price})")

        # Verkaufslogik nur wenn DOGE vorhanden ist
        if doge_balance >= qty:
            sell_price = round(buy_price * (1 + profit_margin), 4)
            session.place_order(
                category=category,
                symbol=symbol,
                side="Sell",
                order_type="Limit",
                qty=qty,
                price=sell_price,
                time_in_force="GTC"
            )
            send_telegram_message(f"📤 Limit-Sell platziert: {qty} DOGE @ {sell_price} USDT")
        else:
            send_telegram_message(f"⛔ Kein DOGE im Wallet – Verkauf wird übersprungen")

    except Exception as e:
        send_telegram_message(f"❌ Allgemeiner Fehler: {str(e)}")

    time.sleep(900)
