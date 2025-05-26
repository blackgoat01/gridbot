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
try:
    session = HTTP(
        api_key=os.getenv("API_KEY"),
        api_secret=os.getenv("API_SECRET")
    )
    # Testverbindung
    session.get_wallet_balance(accountType="UNIFIED")
    send_telegram_message("✅ Verbindung zur Bybit API erfolgreich. Bot startet...")
except Exception as e:
    send_telegram_message(f"❌ API-Verbindungsfehler: {str(e)}")
    exit()

# GridBot-Parameter
symbol = "DOGEUSDT"
category = "spot"
last_price = None
usdt_per_order = 10
profit_margin = 0.01  # 1% Gewinnziel
grid_count = 10
grid_spacing = 0.005  # 0.5 %

while True:
    try:
        response = session.get_tickers(category=category, symbol=symbol)
        price = float(response["result"]["list"][0]["lastPrice"])
        send_telegram_message(f"✅ GridBot läuft (15 Min). DOGEUSDT = {price} USDT")

        # Grid-Berechnung
        grid_prices = [round(price * (1 + grid_spacing) ** i, 4) for i in range(-grid_count // 2, grid_count // 2 + 1)]
        buy_price = min(grid_prices)
        qty = round(usdt_per_order / buy_price, 0)  # ganze Stückzahl DOGE

        # Kaufsignal und Order
        try:
            buy_order = session.place_order(
                category=category,
                symbol=symbol,
                side="Buy",
                order_type="Limit",
                qty=qty,
                price=buy_price,
                time_in_force="GTC"
            )
            send_telegram_message(f"📥 Limit-Buy platziert: {qty} DOGE @ {buy_price} USDT")

            # Wenn Buy erfolgreich platziert wurde, dann verkaufe mit Gewinnziel
            if buy_order.get("retCode") == 0:
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
                send_telegram_message("⚠️ Sell wurde übersprungen, weil Buy nicht erfolgreich war.")

        except Exception as e:
            send_telegram_message(f"⚠️ Fehler bei Orderplatzierung: {str(e)}")

    except Exception as e:
        send_telegram_message(f"❌ Fehler beim Abrufen: {str(e)}")

    time.sleep(900)  # 15 Minuten Pause
