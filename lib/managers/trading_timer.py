from PyQt5.QtCore import QThread, pyqtSignal, QTimer, QTime
import threading
from datetime import datetime, timedelta
import time


class TradingTimer(QThread):
    update_chart_signal = pyqtSignal()  # Сигнал для обновления графика

    def __init__(self, sync_interval=10, delay=0):
        super().__init__()
        self.running = False  # Флаг для контроля потока
        self.sync_interval = sync_interval  # Интервал (15, 30 минут и т.д.)
        self.delay = delay  # Секунды задержки для точности
        self._stop_event = threading.Event()

    def run(self):
        while not self._stop_event.is_set():
            now = datetime.now()
            next_sync = self._get_next_sync_time(now)
            wait_seconds = (next_sync - now).total_seconds() + self.delay
            print(f"Waiting for {wait_seconds} seconds until the next sync.")
            time.sleep(max(0, wait_seconds))
            self.update_chart_signal.emit()  # Отправляем сигнал на обновление графика

    def _get_next_sync_time(self, now):
        """Вычисляем ближайшую временную метку для синхронизации."""
        minute = now.minute
        next_sync_minute = ((minute // self.sync_interval) + 1) * self.sync_interval
        if next_sync_minute >= 60:
            next_sync_minute = 0
            now += timedelta(hours=1)
        next_sync = now.replace(minute=next_sync_minute, second=0, microsecond=0)
        return next_sync

    def stop(self):
        self._stop_event.set()



