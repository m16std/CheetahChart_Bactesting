from PyQt5.QtWidgets import QFileDialog  # type: ignore
from PyQt5.QtGui import *  # type: ignore
import pandas as pd # type: ignore   
import joblib  # type: ignore 

class FileManager:
    def __init__(self, app):
        self.app = app

    def save_candlesticks(self):
        symbol = self.app.symbol_input.currentText()
        interval = self.app.interval_input.currentText()
        limit = self.app.limit_input.value()
        self.app.df = self.app.get_okx_ohlcv(symbol, interval, limit)

        file_name, _ = QFileDialog.getSaveFileName(self.app, "Сохранить свечки", "", "CSV Files (*.csv)")
        if file_name:
            self.app.df.to_csv(file_name)
            print(f"Candlestick data saved to {file_name}")
            return True
        else:
            return False

    def load_candlesticks(self):
        file_name, _ = QFileDialog.getOpenFileName(self.app, "Открыть свечки", "", "CSV Files (*.csv)")
        if file_name:
            self.app.df = pd.read_csv(file_name, index_col=0, parse_dates=True)
            print(f"Candlestick data loaded from {file_name}")
            return True
        return False

    def save_model_dialog(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self.app, "Сохранить модель", "", "Model Files (*.pkl);;All Files (*)", options=options)
        if file_name:
            joblib.dump(self.app.model, file_name)
            return True
        return False

    def load_model_dialog(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self.app, "Открыть модель", "", "Model Files (*.pkl);;All Files (*)", options=options)
        if file_name:
            self.app.model = joblib.load(file_name)
            return True
        return False