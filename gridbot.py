import os
import time
import hmac
import hashlib
import json
import requests
from datetime import datetime

# KONFIGURATION
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


# TELEGRAM SENDEN
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram Fehler:", e)


# ZEIT
def get_timestamp():
    return str(int(time.time() * 1000))


# SIGNATUR V5 (für Body → POST)
def create_signature(secret, payload: dict):
    body_str = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
    return hmac.new(secret.encode(), body_str.encode(), hashlib.sha256).hexdigest()


# ORDER SENDEN
def place_order(side, price, qty):
    url = BASE_URL + "/v5/order/create"
    timestamp = get_timestamp()
    body = {
        "category": "spot",
        "symbol": SYMBOL,
        "side": side,
        "order_type": "Limit",
        "qty": str(qty),
        "price": str(price),
        "time_in_force": "GTC",
        "timestamp": int(timestamp)
    }
    signature = create_signature(API_SECRET, body)
    headers = {
        "X-BAPI-API-KEY": API_KEY,
        "X-BAPI-SIGN": signature,
        "X-BAPI-TIMESTAMP": timestamp,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(body))
        send_telegram(f"{side} Order: {qty} {SYMBOL} @ {price} ➜ Antwort: {response.text}")
    except Exception as e:
        send_telegram(f"❌ Order-Fehler: {e}")


# WALLET-CHECK
def get_wallet_balance():
    url = BASE_URL + "/v5/account/wallet-balance"
    timestamp = get_timestamp()
    params = {
        "accountType": "UNIFIED",
        "timestamp": timestamp
    }
    sign_payload = ''.join([f"{k}={v}" for k, v in sorted(params.items())])
    signature = hmac.new(API_SECRET.encode(), sign_payload.encode(), hashlib.sha256).hexdigest()

    headers = {
        "X-BAPI-API-KEY": API_KEY,
        "X-BAPI-SIGN": signature,
        "X-BAPI-TIMESTAMP": timestamp
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        send_telegram(f"Wallet Check Antwort: {response.text}")
        for item in data["result"]["list"][0]["coin"]:
            if item["coin"] == "DOGE":
                return float(item["availableToTrade"])
        return 0.0
    except Exception as e:
        send_telegram(f"Wallet Fehler: {e}")
        return 0.0


# HAUPTLOOP
def run_bot():
    send_telegram("✅ GridBot wurde erfolgreich gestartet!")

    while True:
        try:
            now = datetime.now().strftime("%H:%M:%S")
            send_telegram(f"✅ GridBot läuft (15 Min). {SYMBOL} = Grid aktiv [{now}]")

            # BUY ORDER
            place_order("Buy", GRID_BUY_PRICE, GRID_QTY)
            time.sleep(5)

            # WALLET CHECK
            balance = get_wallet_balance()
            if balance >= GRID_QTY:
                place_order("Sell", GRID_SELL_PRICE, GRID_QTY)
            else:
                send_telegram("⚠️ Noch nicht genug DOGE vorhanden. Sell wird übersprungen.")
        except Exception as e:
            send_telegram(f"❌ Allgemeiner Fehler: {e}")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    run_bot()
