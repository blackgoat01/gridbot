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
api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
session = HTTP(api_key=api_key, api_secret=api_secret)

# GridBot Konfiguration
symbol = "DOGEUSDT"
category = "spot"
usdt_per_order = 10
profit_margin = 0.01  # 1 %
grid_spacing = 0.005  # 0.5 %
grid_count = 10
last_price = None

# Startnachricht
try:
    session.get_wallet_balance(accountType="UNIFIED")
    send_telegram_message("✅ Verbindung zur Bybit API erfolgreich. Bot startet...")
except Exception as e:
    send_telegram_message(f"❌ API-Verbindungsfehler: {str(e)}")
    exit()

# Bot Loop
while True:
    try:
        ticker = session.get_tickers(category=category, symbol=symbol)
        price = float(ticker["result"]["list"][0]["lastPrice"])
        if price != last_price:
            last_price = price
            send_telegram_message(f"✅ GridBot läuft (15 Min). {symbol} = {price} USDT")

            # Grid-Level
            grid_prices = [round(price * (1 + grid_spacing) ** i, 4)
                           for i in range(-grid_count // 2, grid_count // 2 + 1)]
            buy_price = min(grid_prices)
            qty = round(usdt_per_order / buy_price)  # Runde auf 0 Dezimalstellen für DOGE

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
                send_telegram_message(f"📥 Limit-Buy platziert: {qty} DOGE @ {buy_price} USDT")

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

            except Exception as order_error:
                send_telegram_message(f"⚠️ Fehler bei Orderplatzierung: {order_error}")
        else:
            send_telegram_message("🔁 Kein Preiswechsel – keine neue Order notwendig.")

    except Exception as e:
        send_telegram_message(f"❌ Fehler beim Abruf: {e}")

    time.sleep(900)  # 15 Minuten
