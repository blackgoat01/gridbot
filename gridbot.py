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

# Symbol-Einstellungen
symbol = "DOGEUSDT"
category = "spot"
usdt_per_order = 10
profit_margin = 0.01  # 1 %

# Dezimalstellen pro Symbol (qty)
symbol_precision = {
    "DOGEUSDT": 0,   # Ganze Zahl
    "ETHUSDT": 4,
    "BTCUSDT": 4,
    "SOLUSDT": 2,
    "XRPUSDT": 0,
}

qty_decimals = symbol_precision.get(symbol, 2)  # Fallback: 2 Dezimalstellen

# Hauptlogik
send_telegram_message("✅ Verbindung zur Bybit API wird getestet...")
try:
    wallet = session.get_wallet_balance(accountType="UNIFIED")
    send_telegram_message("✅ Verbindung zur Bybit API erfolgreich. Bot startet...")
except Exception as e:
    send_telegram_message(f"❌ API-Verbindungsfehler: {str(e)}")
    exit()

last_price = None

while True:
    try:
        response = session.get_tickers(category=category, symbol=symbol)
        price = float(response["result"]["list"][0]["lastPrice"])

        if price != last_price:
            last_price = price
            send_telegram_message(f"✅ GridBot läuft (15 Min). {symbol} = {price} USDT")

            # Grid-Level
            grid_count = 10
            grid_spacing = 0.005  # 0.5 %
            grid_prices = [round(price * (1 + grid_spacing) ** i, 4)
                           for i in range(-grid_count//2, grid_count//2 + 1)]

            lowest_buy_price = min(grid_prices)
            qty_raw = usdt_per_order / lowest_buy_price
            qty = round(qty_raw, qty_decimals)

            try:
                # Limit-Buy
                session.place_order(
                    category=category,
                    symbol=symbol,
                    side="Buy",
                    order_type="Limit",
                    qty=qty,
                    price=lowest_buy_price,
                    time_in_force="GTC"
                )
                send_telegram_message(f"📥 Limit-Buy platziert: {qty} {symbol[:-4]} @ {lowest_buy_price} USDT")

                # Zielverkauf mit 1 % Gewinn
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
                send_telegram_message(f"📤 Limit-Sell platziert: {qty} {symbol[:-4]} @ {target_sell_price} USDT")

            except Exception as e:
                send_telegram_message(f"⚠️ Fehler bei Orderplatzierung: {str(e)}")
        else:
            print("Kein Preiswechsel")

    except Exception as e:
        send_telegram_message(f"❌ Fehler beim Abrufen: {str(e)}")

    time.sleep(900)  # 15 Minuten
