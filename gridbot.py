import os
import time
from pybit.unified_trading import HTTP
import requests

# Telegram-Benachrichtigung
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

# Einstellungen
symbol = "DOGEUSDT"
category = "spot"
usdt_per_order = 10
profit_margin = 0.01  # 1 %
grid_spacing = 0.005
grid_count = 10
last_price = None

# Verbindungsprüfung
try:
    session.get_wallet_balance(accountType="UNIFIED")
    send_telegram_message("✅ Verbindung zur Bybit API erfolgreich. Bot startet...")
except Exception as e:
    send_telegram_message(f"❌ API-Verbindungsfehler: {str(e)}")
    exit()

# Hauptschleife
while True:
    try:
        ticker = session.get_tickers(category=category, symbol=symbol)
        price = float(ticker["result"]["list"][0]["lastPrice"])

        if price != last_price:
            last_price = price
            send_telegram_message(f"✅ GridBot läuft (15 Min). {symbol} = {price} USDT")

            # Grid-Level
            grid_prices = [round(price * (1 + grid_spacing) ** i, 4) for i in range(-grid_count//2, grid_count//2 + 1)]
            lowest_buy_price = min(grid_prices)
            qty_raw = usdt_per_order / lowest_buy_price
            qty = float(round(qty_raw, 1))  # DOGE erlaubt nur 1 Nachkommastelle

            # Limit-Kauforder
            try:
                session.place_order(
                    category=category,
                    symbol=symbol,
                    side="Buy",
                    order_type="Limit",
                    qty=qty,
                    price=lowest_buy_price,
                    time_in_force="GTC"
                )
                send_telegram_message(f"📥 Limit-Buy platziert: {qty} DOGE @ {lowest_buy_price} USDT")
            except Exception as e:
                send_telegram_message(f"⚠️ Fehler bei Kauforder: {str(e)}")

            # Zielverkauf (mit Gewinnaufschlag)
            target_price = round(lowest_buy_price * (1 + profit_margin), 4)
            try:
                session.place_order(
                    category=category,
                    symbol=symbol,
                    side="Sell",
                    order_type="Limit",
                    qty=qty,
                    price=target_price,
                    time_in_force="GTC"
                )
                send_telegram_message(f"📤 Limit-Sell platziert: {qty} DOGE @ {target_price} USDT")
            except Exception as e:
                send_telegram_message(f"⚠️ Fehler bei Sellorder: {str(e)}")

        else:
            send_telegram_message("🔁 Kein Preiswechsel – keine neue Order notwendig.")

    except Exception as e:
        send_telegram_message(f"❌ Fehler beim Abrufen: {str(e)}")

    time.sleep(900)  # 15 Minuten
