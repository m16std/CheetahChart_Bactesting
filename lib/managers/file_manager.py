from PyQt5.QtWidgets import QWidget, QFileDialog, QMessageBox  # type: ignore
from PyQt5.QtGui import *  # type: ignore
import pandas as pd # type: ignore   
import joblib  # type: ignore 
import os

class FileManager:
    def __init__(self, app):
        self.app = app

    def save_candlesticks(self):
        file_name, _ = QFileDialog.getSaveFileName(self.app, "Сохранить свечки", "", "CSV Files (*.csv)")
        if file_name:
            self.app.df.to_csv(file_name)
            print(f"Candlestick data saved to {file_name}")
            return True
        else:
            return False

    def load_candlesticks(self, file_name=None):
        """Загружает данные свечей из файла."""
        if not file_name:
            file_name, _ = QFileDialog.getOpenFileName(self.app, "Открыть файл", "", "CSV Files (*.csv)")
        if file_name:
            try:
                self.app.df = pd.read_csv(file_name, index_col=0, parse_dates=True)
                print(f"Candlestick data loaded from {file_name}")
                return True
            except Exception as e:
                QMessageBox.critical(self.app, "Ошибка", f"Не удалось загрузить файл: {e}")
                return False
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
    
    
    def check_strategy_directory(self):
        # Проверяем, существует ли папка стратегий, если нет — открываем диалоговое окно
        strategy_directory = self.load_saved_directory()

        if not strategy_directory or not os.path.exists(strategy_directory):
            QMessageBox.warning(self.app, 'Предупреждение', 'Папка внешних стратегий не найдена. Укажите папку')
            strategy_directory = self.open_directory_selection_dialog()
            return strategy_directory
        else:
            return strategy_directory

    def open_directory_selection_dialog(self):
        # Открываем диалог для выбора директории
        directory = QFileDialog.getExistingDirectory(self.app, 'Выбрать папку внешних стратегий')

        if directory:
            self.save_strategy_directory(directory)
            return directory
        else:
            QMessageBox.warning(self.app, 'Предупреждение', 'Папка не выбрана.')
            return None

    def load_saved_directory(self):
        # Загружаем сохранённую директорию (можно использовать QSettings или просто файл)
        try:
            with open('strategy_directory.txt', 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            return None

    def save_strategy_directory(self, directory):
        # Сохраняем директорию в файл
        with open('strategy_directory.txt', 'w') as f:
            f.write(directory)