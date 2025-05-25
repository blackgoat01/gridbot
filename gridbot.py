
import os
import requests
from pybit import HTTP
from time import sleep

try:
    price = session.ticker_price(symbol="DOGEUSDT")["price"]
    send_telegram_message(f"✅ Preis für DOGEUSDT: {price}")
except Exception as e:
    send_telegram_message(f"⚠️ Preisabruf fehlgeschlagen: {str(e)}")

# Telegram-Funktion
def send_telegram(msg):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": msg})

# Starte-Meldung
send_telegram("✅ GridBot wurde gestartet und ist aktiv.")

# API-Zugang
session = HTTP(
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET")
)

symbol = "ADAUSDT"
usdt_per_order = 10  # z.B. 10 USDT pro Grid
grid_levels = 10
grid_spacing_pct = 1.0  # Abstand in %

def get_price():
    try:
        ticker = session.get_ticker(category="spot", symbol=symbol)
        return float(ticker["result"]["list"][0]["lastPrice"])
    except:
        return None

def place_orders():
    price = get_price()
    if not price:
        send_telegram("⚠️ Fehler beim Abrufen des Preises.")
        return

    prices = []
    for i in range(grid_levels):
        down = round(price * (1 - grid_spacing_pct / 100 * (i + 1)), 4)
        up = round(price * (1 + grid_spacing_pct / 100 * (i + 1)), 4)
        prices.append(("buy", down))
        prices.append(("sell", up))

    for side, p in prices:
        try:
            session.place_active_order(
                category="spot",
                symbol=symbol,
                side="Buy" if side == "buy" else "Sell",
                order_type="Limit",
                qty=round(usdt_per_order / p, 2),
                price=p,
                time_in_force="GTC"
            )
            send_telegram(f"📈 Order {side.upper()} bei {p} gesetzt.")
        except Exception as e:
            send_telegram(f"❌ Fehler bei Order {side} {p}: {e}")

# Hauptloop
while True:
    place_orders()
    send_telegram("✅ Grid-Scan abgeschlossen. Warte 60 min.")
    sleep(3600)
