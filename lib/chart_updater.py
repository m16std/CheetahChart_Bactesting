from PyQt5.QtCore import QThread, pyqtSignal
import time


class ChartUpdater(QThread):
    update_chart_signal = pyqtSignal()  # Сигнал для обновления графика

    def __init__(self, refresh_interval=10):
        super().__init__()
        self.refresh_interval = refresh_interval  # Интервал обновления в секундах
        self.running = False  # Флаг для контроля потока

    def run(self):
        """Метод, который запускается в потоке."""
        while self.running:
            self.update_chart_signal.emit()  # Отправляем сигнал на обновление графика
            time.sleep(self.refresh_interval)

    def start_updating(self):
        """Запускает поток для обновления графика."""
        if not self.isRunning():
            self.running = True
            self.start()

    def stop_updating(self):
        """Останавливает поток обновления графика."""
        self.running = False
        self.wait()

    def set_refresh_interval(self, interval):
        """Метод для изменения частоты обновления."""
        self.refresh_interval = interval
