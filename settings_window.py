from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QMessageBox # type: ignore

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
        self.position_size_input = QLineEdit()

        # Добавляем выпадающий список для выбора вариации позиции
        self.position_type_combo = QComboBox()
        self.position_type_combo.addItem("Процент от баланса")
        self.position_type_combo.addItem("Фиксированная сумма в USDT")
        self.position_type_combo.currentIndexChanged.connect(self.update_position_size_label)

        self.position_size_label = QLabel("Размер позиции (% от баланса)")

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
        layout.addWidget(QLabel("Тип размера позиции"))
        layout.addWidget(self.position_type_combo)
        layout.addWidget(self.position_size_label)
        layout.addWidget(self.position_size_input)

        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)

        self.setLayout(layout)

    def update_position_size_label(self):
        # Меняем единицы измерения в зависимости от выбранной вариации
        if self.position_type_combo.currentIndex() == 0:
            self.position_size_label.setText("Размер позиции (% от баланса)")
        else:
            self.position_size_label.setText("Размер позиции (фиксированная сумма в USDT)")

    def load_settings(self):
        # Загружаем сохраненные значения или устанавливаем по умолчанию
        self.commission_input.setText(self.settings.value("commission", "0.0008"))
        self.initial_balance_input.setText(self.settings.value("initial_balance", "100"))
        self.leverage_input.setText(self.settings.value("leverage", "2"))
        self.profit_factor_input.setText(self.settings.value("profit_factor", "1.5"))
        self.position_type = self.settings.value("position_type", "percent")
        self.position_size = self.settings.value("position_size", "100")
        if self.position_type == "percent":
            self.position_type_combo.setCurrentIndex(0)
        else:
            self.position_type_combo.setCurrentIndex(1)

    def save_settings(self):
        # Сохраняем введенные пользователем значения
        self.settings.setValue("commission", self.commission_input.text())
        self.settings.setValue("initial_balance", self.initial_balance_input.text())
        self.settings.setValue("leverage", self.leverage_input.text())
        self.settings.setValue("profit_factor", self.profit_factor_input.text())
        self.settings.setValue("position_size", self.position_size_input.text())

        # Если выбран фиксированный размер в долларах, проверяем, что он не превышает начальный баланс
        initial_balance = float(self.initial_balance_input.text())
        position_size = float(self.position_size_input.text())
        
        if self.position_type_combo.currentIndex() == 1:  # "Фиксированная сумма в $"
            if position_size > initial_balance:
                QMessageBox.warning(self, "Ошибка", "Размер позиции не может превышать начальный баланс.")
                return
        elif self.position_type_combo.currentIndex() == 0: # "Проценты"
            if position_size > 100:
                QMessageBox.warning(self, "Ошибка", "Размер позиции не может быть больше 100%.")
                return

        if self.position_type_combo.currentIndex() == 0:
            self.settings.setValue("position_type", "percent")
        else:
            self.settings.setValue("position_type", "fixed")
        self.accept()