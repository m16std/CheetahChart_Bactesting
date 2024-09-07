from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton

class SettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Настройки")

        layout = QVBoxLayout()

        self.commission_input = QLineEdit()
        self.initial_balance_input = QLineEdit()
        self.leverage_input = QLineEdit()
        self.profit_factor_input = QLineEdit()

        # Загрузка настроек
        self.load_settings()

        layout.addWidget(QLabel("Торговая комиссия"))
        layout.addWidget(self.commission_input)
        layout.addWidget(QLabel("Начальный баланс"))
        layout.addWidget(self.initial_balance_input)
        layout.addWidget(QLabel("Торговое плечо"))
        layout.addWidget(self.leverage_input)
        layout.addWidget(QLabel("Профит фактор"))
        layout.addWidget(self.profit_factor_input)

        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)

        self.setLayout(layout)

    def load_settings(self):
        # Загружаем сохраненные значения или устанавливаем по умолчанию
        self.commission_input.setText(self.settings.value("commission", "0.0008"))
        self.initial_balance_input.setText(self.settings.value("initial_balance", "100"))
        self.leverage_input.setText(self.settings.value("leverage", "2"))
        self.profit_factor_input.setText(self.settings.value("profit_factor", "1.5"))

    def save_settings(self):
        # Сохраняем введенные пользователем значения
        self.settings.setValue("commission", self.commission_input.text())
        self.settings.setValue("initial_balance", self.initial_balance_input.text())
        self.settings.setValue("leverage", self.leverage_input.text())
        self.settings.setValue("profit_factor", self.profit_factor_input.text())
        self.accept()