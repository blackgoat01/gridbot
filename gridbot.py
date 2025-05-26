import requests
import time
import hmac
import hashlib
import json
from datetime import datetime

# KONFIGURATION
API_KEY = 'DEIN_API_KEY'
API_SECRET = 'DEIN_API_SECRET'
SYMBOL = 'DOGEUSDT'
GRID_QTY = 45
GRID_BUY_PRICE = 0.2182
GRID_SELL_PRICE = 0.2204
CHECK_INTERVAL = 15 * 60  # alle 15 Minuten

BASE_URL = 'https://api.bybit.com'

# SIGNATUR-FUNKTION (für V5)
def create_signature(params, api_secret):
    sorted_params = sorted(params.items())
    query_string = "".join([str(k) + str(v) for k, v in sorted_params])
    return hmac.new(bytes(api_secret, "utf-8"), bytes(query_string, "utf-8"), hashlib.sha256).hexdigest()

# ZEITSTEMPEL
def get_timestamp():
    return int(time.time() * 1000)

# HEADERS
def get_headers():
    return {
        "X-BAPI-API-KEY": API_KEY,
        "X-BAPI-SIGN": "",
        "Content-Type": "application/json"
    }

# WALLET ABFRAGEN
def get_wallet_balance():
    url = BASE_URL + "/v5/account/wallet-balance?accountType=UNIFIED"
    headers = get_headers()
    timestamp = get_timestamp()
    params = {
        "accountType": "UNIFIED",
        "coin": "DOGE",
        "timestamp": timestamp
    }
    signature = create_signature(params, API_SECRET)
    headers["X-BAPI-SIGN"] = signature
    response = requests.get(url, headers=headers, params=params)
    try:
        data = response.json()
        doge = float(data['result']['list'][0]['coin'][0]['availableBalance'])
        return doge
    except Exception as e:
        print("Wallet Fehler:", e)
        return 0.0

# ORDER PLATZIEREN

def place_order(side, price, qty):
    url = BASE_URL + "/v5/order/create"
    body = {
        "category": "spot",
        "symbol": SYMBOL,
        "side": side,
        "order_type": "Limit",
        "qty": str(qty),
        "price": str(price),
        "time_in_force": "GTC",
        "timestamp": get_timestamp()
    }
    signature = create_signature(body, API_SECRET)
    headers = get_headers()
    headers["X-BAPI-SIGN"] = signature
    response = requests.post(url, headers=headers, data=json.dumps(body))
    print(f"{side} Order: {qty} {SYMBOL} @ {price} ➜ Antwort: {response.text}")

# HAUPTFUNKTION

def run_grid_bot():
    while True:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] GridBot startet ...")

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
            print("⚠️ Noch nicht genug DOGE vorhanden. Sell wird übersprungen.")

        # 4. Pause
        print(f"✅ Nächster Durchlauf in {CHECK_INTERVAL / 60} Minuten...")
        time.sleep(CHECK_INTERVAL)

# START
if __name__ == '__main__':
    run_grid_bot()
