from PyQt5.QtGui import *  # type: ignore
from PyQt5.QtCore import QThread, pyqtSignal # type: ignore
import requests # type: ignore
import pandas as pd # type: ignore
from pyqttoast import Toast, ToastPreset

class DataDownloadThread(QThread):
    # Сигнал завершения скачивания
    data_downloaded = pyqtSignal(object)
    show_toast = pyqtSignal(object, object, object)
    # Сигнал обновления прогресс-бара
    progress_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super(DataDownloadThread, self).__init__(parent)

    def __init__(self, symbol, interval, limit, mode = 0, parent=None):
        super(DataDownloadThread, self).__init__(parent)
        self.symbol = symbol
        self.interval = interval
        self.limit = limit
        self.mode = mode

    def run(self):
        # Запускаем метод скачивания данных с переданными параметрами
        if self.mode == 0:
            data = self.get_okx_ohlcv(self.symbol, self.interval, self.limit)
            if len(data) == 1:
                self.show_toast.emit(ToastPreset.ERROR, 'Ошибка загрузки цен. Скорее всего нет интернета или не отвечает апи okx.com',  f"{data[0]}")
            else:
                self.data_downloaded.emit(data)

        if self.mode == 1:
            price = self.get_crypto_price(self.symbol)
            self.data_downloaded.emit(price)
        

        
    def get_okx_ohlcv(self, symbol, interval, limit):
        try:
            url = f'https://www.okx.com/api/v5/market/candles'
            params = {
                'instId': symbol,
                'bar': interval,
                'limit': 300
            }
            data = []
            response = requests.get(url, params=params)
            response = response.json()['data']
            data.extend(response)
            url = f'https://www.okx.com/api/v5/market/history-candles'
            while len(data) < limit:
                self.progress_changed.emit(round(len(data) / limit*100)) 
                params = {
                    'instId': symbol,
                    'bar': interval,
                    'limit': 100,
                    'after': data[-1][0]
                }
                response = requests.get(url, params=params)
                response = response.json()['data']
                data.extend(response)

        except Exception as e:
            return [e]
        
        self.progress_changed.emit(100) 
        data = data[::-1]

        data = pd.DataFrame(data, columns=['ts', 'open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote', 'confirm'])
        data['ts'] = pd.to_numeric(data['ts'], errors='coerce')
        data['ts'] = pd.to_datetime(data['ts'], unit='ms')
        data[['open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote']] = data[['open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote']].astype(float)
        data.set_index('ts', inplace=True)

        return data

    def get_coins(self):
        """Загружает список популярных криптовалют и их иконки"""
        try:
            url = "https://min-api.cryptocompare.com/data/top/mktcapfull?limit=20&tsym=USD"
            response = requests.get(url)
            data = response.json()
            return data
        except Exception as e:
            self.show_toast.emit(ToastPreset.ERROR, 'Ошибка загрузки иконок валют. Скорее всего нет интернета или не отвечает апи cryptocompare.com',  f"{e}")
            return []

    def get_crypto_price(self, symbol):
        """Функция для получения текущей цены криптовалюты с биржи"""
        try:
            # Пример запроса на OKX (или использовать другой API)
            url = f"https://www.okx.com/api/v5/market/ticker?instId={symbol}"
            response = requests.get(url)
            data = response.json()

            # Парсинг цены из ответа API
            price = data['data'][0]['last'] if 'data' in response.json() else "N/A"
            return price
        except Exception as e:
            print(f"Error fetching price: {e}")
            return "N/A"
        