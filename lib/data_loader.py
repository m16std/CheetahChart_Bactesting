from PyQt5.QtGui import *  # type: ignore
from PyQt5.QtCore import QThread, pyqtSignal # type: ignore
import requests # type: ignore
import pandas as pd # type: ignore


class DataDownloadThread(QThread):
    # Сигнал завершения скачивания
    data_downloaded_save_it = pyqtSignal(object)
    data_downloaded_run_it = pyqtSignal(object)
    request_exception = pyqtSignal()
    # Сигнал обновления прогресс-бара
    progress_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super(DataDownloadThread, self).__init__(parent)

    def __init__(self, symbol, interval, limit, run_or_save, parent=None):
        super(DataDownloadThread, self).__init__(parent)
        self.symbol = symbol
        self.interval = interval
        self.limit = limit
        self.run_or_save = run_or_save

    def run(self):
        # Запускаем метод скачивания данных с переданными параметрами
        data = self.get_okx_ohlcv(self.symbol, self.interval, self.limit)

        # После завершения сигнализируем об этом
        if len(data) == 0:
            self.request_exception.emit()
        else:
            if self.run_or_save:
                self.data_downloaded_run_it.emit(data)
            else:
                self.data_downloaded_save_it.emit(data)

        
    def get_okx_ohlcv(self, symbol, interval, limit):
        url = f'https://www.okx.com/api/v5/market/candles'
        params = {
            'instId': symbol,
            'bar': interval,
            'limit': 300
        }
        data = []
        try:
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
        except requests.exceptions.RequestException as err:
            print(f"Error: {err}")
            return []
        
        self.progress_changed.emit(100) 
        data = data[::-1]

        data = pd.DataFrame(data, columns=['ts', 'open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote', 'confirm'])
        data['ts'] = pd.to_numeric(data['ts'], errors='coerce')
        data['ts'] = pd.to_datetime(data['ts'], unit='ms')
        data[['open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote']] = data[['open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote']].astype(float)
        data.set_index('ts', inplace=True)

        return data
