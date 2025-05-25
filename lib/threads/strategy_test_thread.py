from PyQt5.QtCore import QThread, pyqtSignal

class StrategyTestThread(QThread):
    progress_changed = pyqtSignal(int)
    calculation_complete = pyqtSignal(list, object, list)

    def __init__(self, strategy_manager, df, initial_balance, position_size, position_type, profit_factor, commission, parent=None):
        super().__init__(parent)
        self.strategy_manager = strategy_manager
        self.df = df
        self.initial_balance = initial_balance
        self.position_size = position_size
        self.position_type = position_type
        self.profit_factor = profit_factor
        self.commission = commission

    def run(self):
        try:
            self.strategy_manager.df = self.df
            self.strategy_manager.initial_balance = self.initial_balance
            self.strategy_manager.position_size = self.position_size
            self.strategy_manager.position_type = self.position_type
            self.strategy_manager.profit_factor = self.profit_factor
            self.strategy_manager.commission = self.commission
            # Set current strategy name from parent window
            if hasattr(self.strategy_manager.parent(), 'strat_input'):
                self.strategy_manager.strat_name = self.strategy_manager.parent().strat_input.currentText()
            
            self.strategy_manager.run_strategy()
            
            self.calculation_complete.emit(
                self.strategy_manager.positions,
                self.strategy_manager.balance,
                self.strategy_manager.indicators
            )
        except Exception as e:
            print(f"Error in strategy test thread: {str(e)}")
            self.calculation_complete.emit([], [], [])
