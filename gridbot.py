import os
import time
import hmac
import hashlib
import json
import requests
from datetime import datetime

# ENV Variablen laden
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

BASE_URL = "https://api.bybit.com"
SYMBOL = "DOGEUSDT"
GRID_QTY = 45
GRID_BUY_PRICE = 0.2182
GRID_SELL_PRICE = 0.2204
CHECK_INTERVAL = 15 * 60

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg}
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram Error:", e)

def get_timestamp():
    return str(int(time.time() * 1000))

def sign_request(payload: str, secret: str):
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()

def make_headers(payload: str):
    return {
        "X-BAPI-API-KEY": API_KEY,
        "X-BAPI-SIGN": sign_request(payload, API_SECRET),
        "X-BAPI-TIMESTAMP": get_timestamp(),
        "Content-Type": "application/json"
    }

def get_wallet():
    endpoint = "/v5/account/wallet-balance"
    timestamp = get_timestamp()
    query = f"accountType=UNIFIED&coin=DOGE"
    signature = sign_request(f"{timestamp}{API_KEY}{query}", API_SECRET)
    headers = {
        "X-BAPI-API-KEY": API_KEY,
        "X-BAPI-TIMESTAMP": timestamp,
        "X-BAPI-SIGN": signature
    }
    try:
        response = requests.get(BASE_URL + endpoint, params={"accountType": "UNIFIED", "coin": "DOGE"}, headers=headers)
        result = response.json()
        return float(result["result"]["list"][0]["coin"][0]["availableToTrade"])
    except Exception as e:
        send_telegram(f"Wallet Fehler: {str(e)}")
        return 0.0

def place_order(side, price, qty):
    endpoint = "/v5/order/create"
    body = {
        "category": "spot",
        "symbol": SYMBOL,
        "side": side,
        "order_type": "Limit",
        "qty": str(qty),
        "price": str(price),
        "time_in_force": "GTC"
    }
    payload = json.dumps(body)
    headers = make_headers(payload)
    try:
        response = requests.post(BASE_URL + endpoint, headers=headers, data=payload)
        send_telegram(f"{side} Order: {qty} {SYMBOL} @ {price} ➜ Antwort: {response.text}")
    except Exception as e:
        send_telegram(f"Fehler bei {side}: {str(e)}")

def run_bot():
    send_telegram("✅ GridBot wurde erfolgreich gestartet!")
    while True:
        send_telegram(f"✅ GridBot läuft (15 Min). {SYMBOL} Grid aktiv [{datetime.now().strftime('%H:%M:%S')}]")
        place_order("Buy", GRID_BUY_PRICE, GRID_QTY)
        time.sleep(5)
        balance = get_wallet()
        if balance >= GRID_QTY:
            place_order("Sell", GRID_SELL_PRICE, GRID_QTY)
        else:
            send_telegram("⚠️ Noch nicht genug DOGE vorhanden. Sell wird übersprungen.")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    run_bot()
