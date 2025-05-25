from PyQt5.QtCore import QThread, pyqtSignal
import time

from lib.api.okx_load_api import DataDownloadThread

class PriceTimer(QThread):
    new_price_signal = pyqtSignal(object)  # Сигнал для обновления графика
    def __init__(self, refresh_interval=10):
        super().__init__()
        self.refresh_interval = refresh_interval  # Интервал обновления в секундах
        self.running = False  # Флаг для контроля потока
        self.price_download_thread = DataDownloadThread('BTC-USDT', 0, 0, 1)
        self.price_download_thread.data_downloaded.connect(self.return_price)

    def run(self):
        """Метод, который запускается в потоке."""
        while self.running:
            self.price_download_thread.run()
            time.sleep(self.refresh_interval)

    def start_updating(self):
        """Запускает поток для обновления графика."""
        if not self.isRunning():
            self.running = True
            self.start()

    def stop_updating(self):
        """Останавливает поток обновления графика."""
        self.running = False
        self.wait()  # Ждем завершения потока

    def set_refresh_interval(self, interval):
        """Метод для изменения частоты обновления."""
        self.refresh_interval = interval

    def return_price(self, price):
        self.new_price_signal.emit(price)

    def update_symbol(self, symbol):
        self.price_download_thread.symbol = symbol