import requests
import time
import hmac
import hashlib
import json
import os
from datetime import datetime

# KONFIGURATION
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SYMBOL = 'DOGEUSDT'
GRID_QTY = 45
GRID_BUY_PRICE = 0.2182
GRID_SELL_PRICE = 0.2204
CHECK_INTERVAL = 15 * 60  # alle 15 Minuten

BASE_URL = 'https://api.bybit.com'

# TELEGRAM SENDEN
def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        requests.post(url, data=payload)
    except Exception as e:
        print("Telegram Fehler:", e)

# SIGNATUR-FUNKTION (für V5 GET & POST)
def create_signature(data, api_secret, is_body=False):
    if is_body:
        payload = json.dumps(data)
    else:
        sorted_params = sorted(data.items())
        payload = ''.join([f'{k}={v}' for k, v in sorted_params])
    return hmac.new(api_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()

# ZEITSTEMPEL
def get_timestamp():
    return int(time.time() * 1000)

# HEADERS
def get_headers():
    return {
        "X-BAPI-API-KEY": API_KEY,
        "Content-Type": "application/json"
    }

# WALLET ABFRAGEN
def get_wallet_balance():
    url = BASE_URL + "/v5/account/wallet-balance"
    timestamp = get_timestamp()
    params = {
        "accountType": "UNIFIED",
        "coin": "DOGE",
        "timestamp": timestamp
    }
    signature = create_signature(params, API_SECRET, is_body=False)
    headers = get_headers()
    headers["X-BAPI-SIGN"] = signature
    headers["X-BAPI-TIMESTAMP"] = str(timestamp)
    response = requests.get(url, headers=headers, params=params)
    try:
        data = response.json()
        doge = float(data['result']['list'][0]['coin'][0]['availableBalance'])
        return doge
    except Exception as e:
        send_telegram_message(f"Wallet Fehler: {e}")
        return 0.0

# ORDER PLATZIEREN
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
        "timestamp": timestamp
    }
    signature = create_signature(body, API_SECRET, is_body=True)
    headers = get_headers()
    headers["X-BAPI-SIGN"] = signature
    headers["X-BAPI-TIMESTAMP"] = str(timestamp)
    response = requests.post(url, headers=headers, data=json.dumps(body))
    result = f"{side} Order: {qty} {SYMBOL} @ {price} \u2794 Antwort: {response.text}"
    print(result)
    send_telegram_message(result)

# HAUPTFUNKTION
def run_grid_bot():
    send_telegram_message("\u2705 GridBot wurde erfolgreich gestartet!")
    while True:
        now = datetime.now().strftime('%H:%M:%S')
        print(f"\n[{now}] GridBot startet ...")

        # 1. Buy setzen
        place_order("Buy", GRID_BUY_PRICE, GRID_QTY)
        time.sleep(5)

        # 2. Prüfen ob DOGE im Wallet
        doge_balance = get_wallet_balance()
        print("Verfügbare DOGE im Wallet:", doge_balance)

        if doge_balance >= GRID_QTY:
            # 3. Sell setzen
            place_order("Sell", GRID_SELL_PRICE, GRID_QTY)
        else:
            warn = "\u26a0\ufe0f Noch nicht genug DOGE vorhanden. Sell wird übersprungen."
            print(warn)
            send_telegram_message(warn)

        print(f"\u2705 Nächster Durchlauf in {CHECK_INTERVAL / 60} Minuten...")
        time.sleep(CHECK_INTERVAL)

# START
if __name__ == '__main__':
    run_grid_bot()
