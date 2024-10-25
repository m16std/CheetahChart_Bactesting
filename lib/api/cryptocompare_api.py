from pyqttoast import Toast, ToastPreset
from PyQt5.QtCore import QThread, pyqtSignal # type: ignore
from PyQt5.QtGui import QPixmap
import requests
import os

class CryptocompareApi(QThread):
    show_toast = pyqtSignal(object, object, object)
    def load_icon_from_url(self, coin, icon_dir):
        """Загружает иконку с сервера и сохраняет её в локальную директорию"""
        url = f"https://www.cryptocompare.com{coin['CoinInfo']['ImageUrl']}"
        crypto_name = coin['CoinInfo']['Name']
        icon_path = os.path.join(icon_dir, f"{crypto_name}.png")

        try:
            response = requests.get(url)
            if response.status_code == 200:
                with open(icon_path, 'wb') as f:
                    f.write(response.content)
                pixmap = QPixmap(icon_path)
                return pixmap
            else:
                raise ValueError("Ошибка загрузки иконки с сервера")
        except Exception as e:
            #QMessageBox.warning(self, "Ошибка загрузки иконки", f"Ошибка: {str(e)}")
            print(f"Error: {e}")
            return QPixmap()  # Пустая иконка, если произошла ошибка
        
    def get_coins(self):
        """Загружает список популярных криптовалют и их иконки"""
        try:
            url = "https://min-api.cryptocompare.com/data/top/mktcapfull?limit=30&tsym=USD"
            response = requests.get(url)
            data = response.json()
            return data
        except Exception as e:
            self.show_toast.emit(ToastPreset.ERROR, 'Ошибка загрузки иконок валют. Скорее всего нет интернета или не отвечает апи cryptocompare.com',  f"{e}")
            return []