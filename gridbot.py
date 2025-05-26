import os
import time
import hmac
import hashlib
import json
import requests
from datetime import datetime

# === Konfiguration ===
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SYMBOL = "DOGEUSDT"
GRID_QTY = 45
GRID_BUY_PRICE = 0.2182
GRID_SELL_PRICE = 0.2204
CHECK_INTERVAL = 15 * 60  # alle 15 Minuten

BASE_URL = "https://api.bybit.com"
RECV_WINDOW = 5000

# === Telegram ===
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg}
    try:
        requests.post(url, data=payload)
    except:
        pass

# === Signatur erzeugen ===
def create_signature(timestamp, body):
    message = str(timestamp) + API_KEY + str(RECV_WINDOW) + body
    return hmac.new(API_SECRET.encode(), message.encode(), hashlib.sha256).hexdigest()

# === Header generieren ===
def get_headers(signature, timestamp):
    return {
        "X-BAPI-API-KEY": API_KEY,
        "X-BAPI-SIGN": signature,
        "X-BAPI-TIMESTAMP": str(timestamp),
        "X-BAPI-RECV-WINDOW": str(RECV_WINDOW),
        "Content-Type": "application/json"
    }

# === Order senden ===
def place_order(side, price, qty):
    path = "/v5/order/create"
    url = BASE_URL + path
    timestamp = int(time.time() * 1000)
    body_dict = {
        "category": "spot",
        "symbol": SYMBOL,
        "side": side,
        "order_type": "Limit",
        "qty": str(qty),
        "price": str(price),
        "time_in_force": "GTC"
    }
    body_json = json.dumps(body_dict)
    sign = create_signature(timestamp, body_json)
    headers = get_headers(sign, timestamp)

    response = requests.post(url, headers=headers, data=body_json)
    send_telegram(f"{'📩 Buy' if side=='Buy' else '📥 Sell'} {qty} @ {price} \u2794 {response.status_code} - {response.text}")

# === Wallet abrufen ===
def get_wallet_balance():
    path = "/v5/account/wallet-balance"
    url = BASE_URL + path
    timestamp = int(time.time() * 1000)
    params = {
        "accountType": "UNIFIED"
    }
    body = ""
    sign = create_signature(timestamp, body)
    headers = get_headers(sign, timestamp)

    try:
        response = requests.get(url, headers=headers, params=params)
        result = response.json()
        coins = result['result']['list'][0]['coin']
        for c in coins:
            if c['coin'] == 'DOGE':
                return float(c['availableToTrade'])
    except Exception as e:
        send_telegram(f"Wallet Fehler: {str(e)}")
        return 0.0

# === GridBot starten ===
def run_bot():
    send_telegram("\u2705 GridBot wurde gestartet!")
    while True:
        price = round(get_price(), 5)
        send_telegram(f"\u2705 GridBot läuft (15 Min). {SYMBOL} Grid aktiv [{datetime.now().strftime('%H:%M:%S')}]")

        place_order("Buy", GRID_BUY_PRICE, GRID_QTY)
        time.sleep(3)

        balance = get_wallet_balance()
        if balance >= GRID_QTY:
            place_order("Sell", GRID_SELL_PRICE, GRID_QTY)
        else:
            send_telegram("\u26a0 Noch nicht genug DOGE für Verkauf.")

        time.sleep(CHECK_INTERVAL)

# === Preis abfragen ===
def get_price():
    url = BASE_URL + "/v5/market/tickers?category=spot&symbol=" + SYMBOL
    try:
        r = requests.get(url)
        return float(r.json()['result']['list'][0]['lastPrice'])
    except:
        return 0.0

if __name__ == '__main__':
    run_bot()
