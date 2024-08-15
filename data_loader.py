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
        data = self.app.get_okx_ohlcv(symbol, interval, limit)
        self.app.df = pd.DataFrame(data, columns=['ts', 'open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote', 'confirm'])
        self.app.df[['open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote']] = self.app.df[['open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote']].astype(float)
        self.app.df['ts'] = pd.to_datetime(self.app.df['ts'], unit='ms')
        self.app.df.set_index('ts', inplace=True)

        file_name, _ = QFileDialog.getSaveFileName(self.app, "Save Candlestick Data", "", "CSV Files (*.csv)")
        if file_name:
            self.app.df.to_csv(file_name)
            print(f"Candlestick data saved to {file_name}")
        else:
            print('suka')

    def load_candlesticks(self):
        file_name, _ = QFileDialog.getOpenFileName(self.app, "Load Candlestick Data", "", "CSV Files (*.csv)")
        if file_name:
            self.app.df = pd.read_csv(file_name, index_col=0, parse_dates=True)
            print(f"Candlestick data loaded from {file_name}")
            self.app.run_strategy()

    def save_model_dialog(self):
        """Открывает диалоговое окно для сохранения модели."""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self.app, "Сохранить модель", "", "Model Files (*.pkl);;All Files (*)", options=options)
        if file_name:
            joblib.dump(self.app.model, file_name)

    def load_model_dialog(self):
        """Открывает диалоговое окно для загрузки модели."""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self.app, "Загрузить модель", "", "Model Files (*.pkl);;All Files (*)", options=options)
        if file_name:
            self.app.model = joblib.load(file_name)