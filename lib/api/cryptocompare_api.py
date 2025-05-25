from pyqttoast import ToastPreset
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QPixmap
import requests
import os

class CryptocompareApi(QThread):
    show_toast = pyqtSignal(object, object, object)

    def get_coins(self):
        """Загружает список популярных криптовалют."""
        try:
            url = "https://min-api.cryptocompare.com/data/top/mktcapfull?limit=30&tsym=USD"
            response = requests.get(url)
            return response.json()
        except Exception as e:
            self.show_toast.emit(ToastPreset.ERROR, 'Ошибка загрузки данных валют.', f"{e}")
            return []

    def load_icon_from_url(self, coin, icon_dir):
        """Загружает иконку с сервера и сохраняет её в локальную директорию."""
        try:
            url = f"https://www.cryptocompare.com{coin['CoinInfo']['ImageUrl']}"
            crypto_name = coin['CoinInfo']['Name']
            icon_path = os.path.join(icon_dir, f"{crypto_name}.png")

            response = requests.get(url)
            if response.status_code == 200:
                os.makedirs(icon_dir, exist_ok=True)
                with open(icon_path, 'wb') as f:
                    f.write(response.content)
                return QPixmap(icon_path)
        except Exception as e:
            self.show_toast.emit(ToastPreset.ERROR, 'Ошибка загрузки иконки', str(e))
        return QPixmap()  # Return empty pixmap if failed

class CryptoIconLoader:
    def __init__(self, icon_dir):
        self.icon_dir = icon_dir

    def load_icon_from_url(self, coin):
        """Загружает иконку с сервера и сохраняет её в локальную директорию."""
        url = f"https://www.cryptocompare.com{coin['CoinInfo']['ImageUrl']}"
        crypto_name = coin['CoinInfo']['Name']
        icon_path = os.path.join(self.icon_dir, f"{crypto_name}.png")

        try:
            response = requests.get(url)
            if response.status_code == 200:
                with open(icon_path, 'wb') as f:
                    f.write(response.content)
                return QPixmap(icon_path)
            else:
                raise ValueError("Ошибка загрузки иконки с сервера")
        except Exception as e:
            print(f"Error: {e}")
            return QPixmap()  # Пустая иконка, если произошла ошибка