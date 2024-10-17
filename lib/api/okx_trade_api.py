import time
import requests

class OKXApi:
    def __init__(self, api_key, api_secret, passphrase):
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        self.base_url = "https://www.okx.com"
    
    def _make_headers(self):
        return {
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': self.api_secret,
            'OK-ACCESS-PASSPHRASE': self.passphrase
        }

    def _send_request(self, method, endpoint, params=None, data=None):
        url = f'{self.base_url}/{endpoint}'
        headers = self._make_headers()
        try:
            response = requests.request(method, url, headers=headers, params=params, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f'Error in API request: {e}')
            return None

    def open_position(self, symbol, qty, posSide, leverage, tp=None, sl=None):
        """Открытие позиции с тейком и стопом (если указаны)."""
        data = {
            'instId': symbol,
            'lever': leverage,
            'tdMode': 'cross',
            'posSide': posSide,
            'ordType': 'market',
            'sz': qty
        }
        if tp:
            data['tpTriggerPx'] = tp
        if sl:
            data['slTriggerPx'] = sl

        return self._send_request('POST', 'trade/order', data=data)

    def close_position(self, symbol, qty, posSide):
        """Закрытие позиции."""
        data = {
            'instId': symbol,
            'posSide': posSide,
            'ordType': 'market',
            'sz': qty
        }
        return self._send_request('POST', 'trade/order', data=data)
    
    def update_take_profit(self, position_id, take_profit):
        """Обновляет тейк-профит на бирже"""
        try:
            # Код для обновления тейк-профита на бирже
            return True
        except Exception as e:
            print(f"Ошибка обновления TP для позиции {position_id}: {e}")
            return False
    
    def update_stop_loss(self, position_id, stop_loss):
        """Обновляет стоп-лосс на бирже"""
        try:
            # Код для обновления стоп-лосса на бирже
            return True
        except Exception as e:
            print(f"Ошибка обновления SL для позиции {position_id}: {e}")
            return False

    def get_open_positions(self):
        """Получение всех открытых позиций."""
        return self._send_request('GET', 'account/positions')

    def get_order(self, order_id):
        """Получение информации по ордеру."""
        params = {'ordId': order_id}
        return self._send_request('GET', 'trade/order', params=params)