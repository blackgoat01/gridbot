import requests
import time
import hmac
import hashlib
import json
import os
from datetime import datetime

# Konfiguration über Umgebungsvariablen
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SYMBOL = "DOGEUSDT"
GRID_QTY = 45
GRID_BUY_PRICE = 0.2182
GRID_SELL_PRICE = 0.2204
CHECK_INTERVAL = 15 * 60

BASE_URL = "https://api.bybit.com"

# Telegram-Funktion
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
        requests.post(url, data=payload)
    except Exception as e:
        print("Telegram Fehler:", e)

# Signatur erstellen für POST (Body-Hashing)
def create_signature(body: str, secret: str):
    return hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()

# Zeitstempel
def get_timestamp():
    return str(int(time.time() * 1000))

# Header für V5
def get_headers(signature, timestamp):
    return {
        "X-BAPI-API-KEY": API_KEY,
        "X-BAPI-SIGN": signature,
        "X-BAPI-TIMESTAMP": timestamp,
        "Content-Type": "application/json"
    }

# Wallet-Check
def get_wallet_balance():
    url = f"{BASE_URL}/v5/account/wallet-balance?accountType=UNIFIED"
    timestamp = get_timestamp()
    headers = {
        "X-BAPI-API-KEY": API_KEY,
        "X-BAPI-TIMESTAMP": timestamp,
        "Content-Type": "application/json"
    }
    body = {}
    signature = create_signature("", API_SECRET)
    headers["X-BAPI-SIGN"] = signature
    response = requests.get(url, headers=headers)
    try:
        data = response.json()
        balance = data["result"]["list"][0]["coin"]
        for c in balance:
            if c["coin"] == "DOGE":
                return float(c["availableBalance"])
        return 0.0
    except Exception as e:
        send_telegram(f"Wallet Fehler: {str(e)}")
        return 0.0

# Order platzieren
def place_order(side, price, qty):
    url = f"{BASE_URL}/v5/order/create"
    timestamp = get_timestamp()
    body = {
        "category": "spot",
        "symbol": SYMBOL,
        "side": side,
        "order_type": "Limit",
        "qty": str(qty),
        "price": str(price),
        "time_in_force": "GTC"
    }
    body_str = json.dumps(body)
    signature = create_signature(body_str, API_SECRET)
    headers = get_headers(signature, timestamp)
    response = requests.post(url, headers=headers, data=body_str)
    send_telegram(f"{side} Order: {qty} {SYMBOL} @ {price} ➜ Antwort: {response.text}")

# GridBot
def run_bot():
    send_telegram("✅ GridBot wurde erfolgreich gestartet!")
    while True:
        try:
            current = datetime.now().strftime("%H:%M:%S")
            send_telegram(f"✅ GridBot läuft ({CHECK_INTERVAL // 60} Min). {SYMBOL} = Grid aktiv [{current}]")
            place_order("Buy", GRID_BUY_PRICE, GRID_QTY)
            time.sleep(5)
            wallet = get_wallet_balance()
            if wallet >= GRID_QTY:
                place_order("Sell", GRID_SELL_PRICE, GRID_QTY)
            else:
                send_telegram("⚠️ Noch nicht genug DOGE vorhanden. Sell wird übersprungen.")
            time.sleep(CHECK_INTERVAL)
        except Exception as e:
            send_telegram(f"❌ Fehler im Bot: {str(e)}")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    run_bot()
