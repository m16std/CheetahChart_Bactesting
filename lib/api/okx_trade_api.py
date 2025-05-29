import requests
import json
import websocket
import base64
import hmac
import hashlib
import time
from threading import Thread
from datetime import datetime, timezone

class OKXApi:
    def __init__(self, api_key, api_secret, passphrase):
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        self.base_url = "https://www.okx.com"

    def _make_headers(self, method, endpoint, body=""):
        # Ensure credentials are set
        if not self.api_key or not self.api_secret or not self.passphrase:
            raise ValueError("API credentials are not set.")

        # Generate the current UTC timestamp with millisecond precision
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        message = f"{timestamp}{method}{endpoint}{body}"
        signature = base64.b64encode(
            hmac.new(
                self.api_secret.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')

        return {
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }

    def _send_request(self, method, endpoint, params=None, data=None):
        url = f"{self.base_url}{endpoint}"
        headers = self._make_headers(method, endpoint, body=json.dumps(data) if data else "")
        try:
            response = requests.request(method, url, headers=headers, params=params, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f'Error in API request: {e}')
            return None

    def get_order_book(self, symbol, depth=5):
        endpoint = f"/api/v5/market/books"
        params = {"instId": symbol, "sz": depth}
        return self._send_request("GET", endpoint, params=params)

    def place_limit_order(self, symbol, qty, price, posSide, side):
        data = {
            'instId': symbol,
            'tdMode': 'cross',
            'posSide': posSide,
            'ordType': 'limit',
            'sz': qty,
            'px': price,
            'side': side
        }
        return self._send_request('POST', '/api/v5/trade/order', data=data)

    def cancel_order(self, order_id, symbol):
        data = {
            'instId': symbol,
            'ordId': order_id
        }
        return self._send_request('POST', '/api/v5/trade/cancel-order', data=data)

    def get_trade_history(self, symbol, limit=10):
        endpoint = f"/api/v5/market/trades"
        params = {"instId": symbol, "limit": limit}
        return self._send_request("GET", endpoint, params=params)

    def get_account_balance(self):
        try:
            endpoint = "/api/v5/account/balance"
            response = self._send_request("GET", endpoint)
            if response and 'data' in response:
                balances = response['data'][0]['details']
                current_balance = sum(float(balance['eqUsd']) for balance in balances)  # Используем 'eqUsd'
                return current_balance
        except Exception as e:
            print(f"Error fetching balance: {e}")
        return 0

    def get_position_risk(self):
        endpoint = "/api/v5/account/positions"
        return self._send_request("GET", endpoint)

    def open_position(self, symbol, qty, posSide, leverage, tp=0, sl=0):
        data = {
            'instId': symbol,
            'lever': leverage,
            'tdMode': 'cross',
            'posSide': posSide,
            'ordType': 'market',
            'sz': qty
        }
        if tp != 0:
            data['tpTriggerPx'] = tp
            data['tpOrdPx'] = '-1'
        if sl != 0:
            data['slTriggerPx'] = sl
            data['slOrdPx'] = '-1'

        response = self._send_request('POST', '/api/v5/trade/order', data=data)
        if response and 'data' in response and len(response['data']) > 0:
            return response['data'][0].get('ordId')
        return None

    def close_position(self, symbol, posId, posSide):
        data = {
            'instId': symbol,
            'posId': posId,
            'posSide': posSide,
            'mgnMode': 'cross',
            'ordType': 'market',
            'closePosition': True
        }
        return self._send_request('POST', '/api/v5/trade/close-position', data=data)

    def update_take_profit(self, symbol, posSide, tp):
        data = {
            'instId': symbol,
            'posSide': posSide,
            'tpTriggerPx': tp,
            'tpOrdPx': '-1'
        }
        return self._send_request('POST', '/api/v5/trade/order-algo', data=data)

    def update_stop_loss(self, symbol, posSide, sl):
        data = {
            'instId': symbol,
            'posSide': posSide,
            'slTriggerPx': sl,
            'slOrdPx': '-1'
        }
        return self._send_request('POST', '/api/v5/trade/order-algo', data=data)

    def get_open_positions(self):
        """Fetch all positions from the API."""
        endpoint = "account/positions"
        return self._send_request("GET", endpoint)

    def get_order(self, order_id):
        params = {'ordId': order_id}
        return self._send_request('GET', 'trade/order', params=params)
    
    def validate_credentials(self):
        try:
            response = self.get_account_balance()
            if response and 'data' in response:
                print("API credentials are valid.")
                return True
            else:
                print("Invalid API credentials or insufficient permissions.")
                return False
        except Exception as e:
            print(f"Error validating API credentials: {str(e)}")
            return False

    def get_position_history(self):
        """Fetch the history of all positions from the API."""
        endpoint = "/api/v5/account/positions-history"
        return self._send_request("GET", endpoint)

    def test_api_credentials(self):
        test_results = {}

        try:
            response = self.get_account_balance()
            test_results['get_account_balance'] = response if response else "Failed"
        except Exception as e:
            test_results['get_account_balance'] = f"Error: {str(e)}"

        try:
            response = self.get_position_risk()
            test_results['get_position_risk'] = response if response else "Failed"
        except Exception as e:
            test_results['get_position_risk'] = f"Error: {str(e)}"

        try:
            response = self.place_limit_order(
                symbol="BTC-USDT",
                qty="0.001",
                price="1000000",
                posSide="long",
                side="buy"
            )
            test_results['place_limit_order'] = response if response else "Failed"
        except Exception as e:
            test_results['place_limit_order'] = f"Error: {str(e)}"

        try:
            response = self.get_order_book(symbol="BTC-USDT")
            test_results['get_order_book'] = response if response else "Failed"
        except Exception as e:
            test_results['get_order_book'] = f"Error: {str(e)}"

        for test, result in test_results.items():
            print(f"{test}: {result}")

        return test_results

    def get_account_metrics(self):
        """Получение параметров: плавающие PnL, используемая маржа и минимальная маржа."""
        endpoint = "/api/v5/account/account-position-risk"
        response = self._send_request("GET", endpoint)
        if response and 'data' in response:
            data = response['data'][0]
            floating_pnl = float(data.get('upl', 0))  # Плавающие прибыль и убытки
            used_margin = float(data.get('imr', 0))  # Используемая маржа
            min_margin = float(data.get('mmr', 0))  # Минимальная маржа
            return floating_pnl, used_margin, min_margin
        return 0, 0, 0

class OKXWebSocket:
    def __init__(self, api_key, api_secret, passphrase):
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        self.ws_url = "wss://ws.okx.com:8443/ws/v5/public"
        self.ws = None

    def _on_message(self, ws, message):
        print(f"Received message: {message}")

    def _on_error(self, ws, error):
        print(f"WebSocket error: {error}")

    def _on_close(self, ws, close_status_code, close_msg):
        print("WebSocket connection closed")

    def _on_open(self, ws):
        print("WebSocket connection opened")

    def connect_websocket(self):
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open
        )
        thread = Thread(target=self.ws.run_forever)
        thread.start()

    def subscribe_to_ticker(self, symbol):
        if self.ws:
            message = {
                "op": "subscribe",
                "args": [{"channel": "tickers", "instId": symbol}]
            }
            self.ws.send(json.dumps(message))

    def subscribe_to_candles(self, symbol, interval):
        if self.ws:
            message = {
                "op": "subscribe",
                "args": [{"channel": "candle" + interval, "instId": symbol}]
            }
            self.ws.send(json.dumps(message))

    def close_websocket(self):
        if self.ws:
            self.ws.close()

