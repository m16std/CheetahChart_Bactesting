from PyQt5.QtCore import QThread, pyqtSignal
import time

class TradingStatusUpdater(QThread):
    update_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, api, is_trade=False, symbol="", positions=None, timer=None, update_interval=30):
        super().__init__()
        self.api = api
        self.is_trade = is_trade
        self.symbol = symbol
        self.positions = positions
        self.timer = timer
        self.update_interval = update_interval
        self._running = True

    def run(self):
        while self._running:
            try:
                self.update_status()
                time.sleep(self.update_interval)
            except Exception as e:
                self.error_signal.emit(str(e))
                time.sleep(1)  # Короткая пауза при ошибке

    def update_status(self):
        try:
            current_balance = self.api.get_account_balance() if self.api else 0
            floating_pnl, used_margin, min_margin = self.api.get_account_metrics() if self.api else (0, 0, 0)
            time_to_next_cycle = self.timer.remaining_time() if self.timer else "N/A"

            data = {
                "is_active": self.is_trade,
                "current_pair": self.symbol,
                "open_positions": self.positions,
                "time_to_next_cycle": time_to_next_cycle,
                "current_balance": current_balance,
                "floating_pnl": floating_pnl,
                "used_margin": used_margin,
                "min_margin": min_margin,
            }
            self.update_signal.emit(data)
        except Exception as e:
            self.error_signal.emit(str(e))

    def update_params(self, is_trade=None, symbol=None, positions=None, timer=None):
        if is_trade is not None: self.is_trade = is_trade
        if symbol is not None: self.symbol = symbol
        if positions is not None: self.positions = positions
        if timer is not None: self.timer = timer

    def stop(self):
        self._running = False
        self.wait()

