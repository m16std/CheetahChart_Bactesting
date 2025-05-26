from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt

class DataSourceWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выбор источника данных")
        self.setMinimumWidth(300)
        self.selected_source = None

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Выберите источник данных:"))

        self.buttons_layout = QHBoxLayout()

        # OKX Button
        self.okx_button = QPushButton("OKX")
        self.okx_button.setCheckable(True)
        self.okx_button.clicked.connect(lambda: self.select_source("OKX"))
        self.buttons_layout.addWidget(self.okx_button)

        # Binance Button
        self.binance_button = QPushButton("Binance")
        self.binance_button.setCheckable(True)
        self.binance_button.clicked.connect(lambda: self.select_source("Binance"))
        self.buttons_layout.addWidget(self.binance_button)

        # Bybit Button
        self.bybit_button = QPushButton("Bybit")
        self.bybit_button.setCheckable(True)
        self.bybit_button.clicked.connect(lambda: self.select_source("Bybit"))
        self.buttons_layout.addWidget(self.bybit_button)

        layout.addLayout(self.buttons_layout)

        # Confirm Button
        confirm_button = QPushButton("Подтвердить")
        confirm_button.clicked.connect(self.accept)
        layout.addWidget(confirm_button)

        self.setLayout(layout)

    def select_source(self, source):
        """Handle source selection and update button styles."""
        self.selected_source = source
        self.okx_button.setChecked(source == "OKX")
        self.binance_button.setChecked(source == "Binance")
        self.bybit_button.setChecked(source == "Bybit")

        # Update button styles
        self.okx_button.setStyleSheet("border: 2px solid blue;" if source == "OKX" else "")
        self.binance_button.setStyleSheet("border: 2px solid blue;" if source == "Binance" else "")
        self.bybit_button.setStyleSheet("border: 2px solid blue;" if source == "Bybit" else "")
