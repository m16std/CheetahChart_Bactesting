from PyQt5.QtCore import QThread, pyqtSignal, QTimer
import weakref

class TradingStatusUpdater(QThread):
    update_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, app_instance):
        super().__init__()
        self._app = weakref.ref(app_instance)  # Используем weakref для предотвращения циклических ссылок
        self._running = True
        self._timer = QTimer()
        self._timer.timeout.connect(self.update_status)
        self._timer.setInterval(5000)  # 5 секунд между обновлениями

    def run(self):
        self._timer.start()
        self.update_status()  # Первое обновление сразу
        self.exec_()

    def update_status(self):
        """Безопасное обновление статуса с проверками."""
        app = self._app()
        if not app or not self._running:
            self._timer.stop()
            return

        try:
            current_balance = app.trading_sync_manager.api.get_account_balance()
            floating_pnl, used_margin, min_margin = app.trading_sync_manager.api.get_account_metrics()
            
            # Безопасное получение времени до следующего цикла
            time_to_next_cycle = (
                app.timer.remaining_time()
                if hasattr(app, 'timer') and app.timer
                else "N/A"
            )

            data = {
                "is_active": app.is_trade,
                "current_pair": app.symbol_input.currentText(),
                "open_positions": app.positions,
                "time_to_next_cycle": time_to_next_cycle,
                "current_balance": current_balance,
                "floating_pnl": floating_pnl,
                "used_margin": used_margin,
                "min_margin": min_margin,
            }
            self.update_signal.emit(data)
        except Exception as e:
            self.error_signal.emit(str(e))

    def stop(self):
        """Безопасная остановка обновлений."""
        self._running = False
        self._timer.stop()
        self.quit()
        self.wait()
