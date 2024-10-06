from PyQt5.QtGui import QPixmap
import requests
import os

class CryptocompareApi:
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