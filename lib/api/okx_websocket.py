import websocket
import json
from threading import Thread

class OKXWebSocket:
    def __init__(self, ws_url="wss://ws.okx.com:8443/ws/v5/public"):
        self.ws_url = ws_url
        self.ws = None

    def _on_message(self, ws, message):
        print(f"Received message: {message}")

    def _on_error(self, ws, error):
        print(f"WebSocket error: {error}")

    def _on_close(self, ws, close_status_code, close_msg):
        print("WebSocket connection closed")

    def _on_open(self, ws):
        print("WebSocket connection opened")

    def connect(self):
        """Подключение к WebSocket."""
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
        """Подписка на обновления тикера."""
        if self.ws:
            message = {
                "op": "subscribe",
                "args": [{"channel": "tickers", "instId": symbol}]
            }
            self.ws.send(json.dumps(message))

    def subscribe_to_candles(self, symbol, interval):
        """Подписка на обновления свечей."""
        if self.ws:
            message = {
                "op": "subscribe",
                "args": [{"channel": "candle" + interval, "instId": symbol}]
            }
            self.ws.send(json.dumps(message))

    def close(self):
        """Закрытие WebSocket соединения."""
        if self.ws:
            self.ws.close()
