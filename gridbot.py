import os
import time
import hmac
import hashlib
import json
import requests
from datetime import datetime

# === KONFIGURATION AUS ENV ===
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

BASE_URL = "https://api.bybit.com"
SYMBOL = "DOGEUSDT"
GRID_QTY = 45
GRID_BUY_PRICE = 0.2182
GRID_SELL_PRICE = 0.2204
CHECK_INTERVAL = 15 * 60  # 15 Minuten

# === TELEGRAM ===
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": msg}
        requests.post(url, data=payload)
    except Exception as e:
        print("Telegram Fehler:", e)

# === V5 SIGNATUR ===
def get_timestamp():
    return str(int(time.time() * 1000))

def sign_payload(query: str, secret: str):
    return hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()

# === WALLET ABFRAGE ===
def get_wallet_balance():
    endpoint = "/v5/account/wallet-balance"
    timestamp = get_timestamp()
    query_string = f"accountType=UNIFIED&coin=DOGE"
    signature = sign_payload(f"{timestamp}{API_KEY}{query_string}", API_SECRET)
    headers = {
        "X-BAPI-API-KEY": API_KEY,
        "X-BAPI-SIGN": signature,
        "X-BAPI-TIMESTAMP": timestamp
    }
    url = f"{BASE_URL}{endpoint}?{query_string}"
    try:
        res = requests.get(url, headers=headers)
        data = res.json()
        doge_data = data['result']['list'][0]['coin'][0]
        return float(doge_data.get("availableToTrade", 0))
    except Exception as e:
        send_telegram(f"❌ Wallet Fehler: {str(e)}")
        return 0

# === ORDER SENDEN ===
def place_order(side, price, qty):
    endpoint = "/v5/order/create"
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
    body_json = json.dumps(body, separators=(',', ':'), ensure_ascii=False)
    signature = hmac.new(API_SECRET.encode(), body_json.encode(), hashlib.sha256).hexdigest()
    headers = {
        "X-BAPI-API-KEY": API_KEY,
        "X-BAPI-SIGN": signature,
        "X-BAPI-TIMESTAMP": timestamp,
        "Content-Type": "application/json"
    }
    try:
        res = requests.post(BASE_URL + endpoint, headers=headers, data=body_json)
        send_telegram(f"📥 {side} {qty} DOGE @ {price} ➜ {res.status_code} - {res.text}")
    except Exception as e:
        send_telegram(f"❌ Order Fehler: {str(e)}")

# === MAIN LOOP ===
def run():
    send_telegram("✅ GridBot wurde gestartet!")
    while True:
        try:
            now = datetime.now().strftime('%H:%M:%S')
            send_telegram(f"🔄 Prüfung gestartet {now}")
            place_order("Buy", GRID_BUY_PRICE, GRID_QTY)
            time.sleep(5)
            balance = get_wallet_balance()
            if balance >= GRID_QTY:
                place_order("Sell", GRID_SELL_PRICE, GRID_QTY)
            else:
                send_telegram("⚠️ Noch nicht genug DOGE für Verkauf.")
        except Exception as err:
            send_telegram(f"❌ Allgemeiner Fehler: {err}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    run()
