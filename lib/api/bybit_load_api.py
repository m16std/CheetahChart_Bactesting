from PyQt5.QtCore import QThread, pyqtSignal
import requests
import pandas as pd
from pyqttoast import ToastPreset

class BybitAPI(QThread):
    data_downloaded = pyqtSignal(object)
    show_toast = pyqtSignal(object, object, object)
    progress_changed = pyqtSignal(int)

    def __init__(self, symbol=None, interval=None, limit=None, parent=None):
        super().__init__(parent)
        self.base_url = "https://api.bybit.com"
        self.symbol = symbol
        self.interval = interval
        self.limit = limit

    def run(self):
        try:
            data = self.get_ohlcv(self.symbol, self.interval, self.limit)
            if isinstance(data, list) and len(data) == 1:
                self.show_toast.emit(ToastPreset.ERROR, "Ошибка загрузки данных Bybit", data[0])
            else:
                self.data_downloaded.emit(data)
        except Exception as e:
            self.show_toast.emit(ToastPreset.ERROR, "Ошибка", str(e))

    def get_ohlcv(self, symbol, interval, limit):
        try:
            url = f"{self.base_url}/v2/public/kline/list"
            params = {
                "symbol": symbol.replace("-", ""),
                "interval": interval,
                "limit": limit
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            df = pd.DataFrame(data['result'], columns=[
                'ts', 'open', 'high', 'low', 'close', 'volume'
            ])
            df['ts'] = pd.to_datetime(df['ts'], unit='s')
            df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
            df.set_index('ts', inplace=True)
            self.progress_changed.emit(100)
            return df
        except Exception as e:
            return [f"Error fetching Bybit data: {e}"]
