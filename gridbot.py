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

    try:
    account_info = session.get_wallet_balance(accountType="UNIFIED")
    print("✅ Verbindung erfolgreich:", account_info)
    send_telegram_message("✅ Verbindung zur Bybit API erfolgreich. Bot startet...")
except Exception as e:
    print("❌ API-Verbindungsfehler:", e)
    send_telegram_message(f"❌ API-Verbindungsfehler: {str(e)}")
    exit()
)

# GridBot-Logik mit Preisabfrage und Schutz vor doppelten Orders
symbol = "DOGEUSDT"
category = "spot"
last_price = None
usdt_per_order = 10
profit_margin = 0.01  # 1% Gewinnziel pro Trade

while True:
    try:
        response = session.get_tickers(category=category, symbol=symbol)
        price = float(response["result"]["list"][0]["lastPrice"])

        if price != last_price:
            last_price = price
            send_telegram_message(f"✅ GridBot läuft (15 Min). DOGEUSDT = {price} USDT")

            # Grid-Level-Berechnung
            grid_count = 10
            grid_spacing = 0.005  # 0.5 %
            grid_prices = [round(price * (1 + grid_spacing) ** i, 4) for i in range(-grid_count//2, grid_count//2 + 1)]

            # Orderplatzierung bei unterem Grid-Level (Kaufsignal)
            lowest_buy_price = min(grid_prices)
            qty = round(usdt_per_order / lowest_buy_price, 2)
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

                # Ziel-Verkaufspreis mit Gewinnaufschlag
                target_sell_price = round(lowest_buy_price * (1 + profit_margin), 4)
                session.place_order(
                    category=category,
                    symbol=symbol,
                    side="Sell",
                    order_type="Limit",
                    qty=qty,
                    price=target_sell_price,
                    time_in_force="GTC"
                )
                send_telegram_message(f"📤 Limit-Sell platziert: {qty} DOGE @ {target_sell_price} USDT")

            except Exception as e:
                send_telegram_message(f"⚠️ Fehler bei Orderplatzierung: {str(e)}")

        else:
            send_telegram_message("🔁 Kein Preiswechsel – keine neue Order notwendig.")

    except Exception as e:
        send_telegram_message(f"❌ Fehler beim Abrufen: {str(e)}")

    time.sleep(900)  # 15 Minuten
