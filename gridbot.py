import os
import time
from pybit.unified_trading import HTTP
import requests

# Telegram-Benachrichtigung
def send_telegram(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(url, data={"chat_id": chat_id, "text": message})
    except:
        pass

# API-Verbindung
session = HTTP(
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET")
)

symbol = "DOGEUSDT"
category = "spot"
usdt_per_order = 10
profit_margin = 0.01  # 1 % Zielgewinn

send_telegram("✅ Verbindung zur Bybit API erfolgreich. Bot startet...")

last_price = None

while True:
    try:
        ticker = session.get_tickers(category=category, symbol=symbol)
        price = float(ticker["result"]["list"][0]["lastPrice"])

        if price != last_price:
            last_price = price
            send_telegram(f"✅ GridBot läuft (15 Min). DOGEUSDT = {price} USDT")

            grid_count = 10
            grid_spacing = 0.005
            grid_prices = [round(price * (1 + grid_spacing) ** i, 4) for i in range(-grid_count // 2, grid_count // 2 + 1)]
            buy_price = min(grid_prices)

            qty = int(usdt_per_order // buy_price)  # Nur ganze DOGE
            if qty == 0:
                send_telegram("⚠️ Menge zu klein für Kauforder.")
                time.sleep(900)
                continue

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
                send_telegram(f"📤 Limit-Sell platziert: {qty} DOGE @ {sell_price} USDT")

            except Exception as e:
                send_telegram(f"⚠️ Fehler bei Orderplatzierung: {str(e)}")

    except Exception as e:
        send_telegram(f"❌ API-Fehler: {str(e)}")

    time.sleep(900)
