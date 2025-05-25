from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
                           QComboBox, QMessageBox, QSpinBox, QTabWidget, QWidget)

class SettingsWindow(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Настройки")
        self.setMinimumWidth(400)

        layout = QVBoxLayout()

        # Создаем TabWidget
        self.tab_widget = QTabWidget()
        
        # Создаем вкладки
        self.testing_tab = QWidget()
        self.trading_tab = QWidget()
        
        # Добавляем вкладки в TabWidget
        self.tab_widget.addTab(self.testing_tab, "Тестирование")
        self.tab_widget.addTab(self.trading_tab, "Торговля")

        # Инициализируем элементы управления для тестирования
        self.init_testing_tab()
        
        # Инициализируем элементы управления для торговли
        self.init_trading_tab()

        layout.addWidget(self.tab_widget)

        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.validate_fields)
        layout.addWidget(save_button)

        self.setLayout(layout)
        self.load_settings()

    def init_testing_tab(self):
        layout = QVBoxLayout()

        # Настройки для тестирования
        self.commission_input = QLineEdit()
        self.initial_balance_input = QLineEdit()
        self.leverage_input = QLineEdit()
        self.profit_factor_input = QLineEdit()
        self.position_size_input = QLineEdit()

        self.position_type_combo = QComboBox()
        self.position_type_combo.addItem("Процент от баланса")
        self.position_type_combo.addItem("Фиксированная сумма в USDT")
        self.position_type_combo.currentIndexChanged.connect(self.update_position_size_label)

        self.position_size_label = QLabel("Размер позиции (% от баланса)")

        layout.addWidget(QLabel("Торговая комиссия"))
        layout.addWidget(self.commission_input)
        layout.addWidget(QLabel("Начальный баланс (USDT)"))
        layout.addWidget(self.initial_balance_input)
        layout.addWidget(QLabel("Торговое плечо"))
        layout.addWidget(self.leverage_input)
        layout.addWidget(QLabel("Профит фактор"))
        layout.addWidget(self.profit_factor_input)
        layout.addWidget(QLabel("Тип размера позиции"))
        layout.addWidget(self.position_type_combo)
        layout.addWidget(self.position_size_label)
        layout.addWidget(self.position_size_input)

        self.testing_tab.setLayout(layout)

    def init_trading_tab(self):
        layout = QVBoxLayout()

        # Создаем все элементы управления в начале
        self.refresh_interval_input = QSpinBox()
        self.refresh_interval_input.setMinimum(5)
        self.refresh_interval_input.setMaximum(900)
        self.refresh_interval_input.setValue(10)

        # Добавляем торговые настройки
        self.trade_leverage_input = QLineEdit()
        self.trade_profit_factor_input = QLineEdit()
        self.trade_position_size_input = QLineEdit()

        self.trade_position_type_combo = QComboBox()
        self.trade_position_type_combo.addItem("Процент от баланса")
        self.trade_position_type_combo.addItem("Фиксированная сумма в USDT")
        self.trade_position_type_combo.currentIndexChanged.connect(self.update_trade_position_size_label)

        self.trade_position_size_label = QLabel("Размер позиции (% от баланса)")

        layout.addWidget(QLabel("Торговое плечо"))
        layout.addWidget(self.trade_leverage_input)
        layout.addWidget(QLabel("Профит фактор"))
        layout.addWidget(self.trade_profit_factor_input)
        layout.addWidget(QLabel("Тип размера позиции"))
        layout.addWidget(self.trade_position_type_combo)
        layout.addWidget(self.trade_position_size_label)
        layout.addWidget(self.trade_position_size_input)

        layout.addWidget(QLabel("Интервал обновления (сек):"))
        layout.addWidget(self.refresh_interval_input)

        self.trading_tab.setLayout(layout)

    def update_position_size_label(self):
        # Меняем единицы измерения в зависимости от выбранной вариации
        if self.position_type_combo.currentIndex() == 0:
            self.position_size_label.setText("Размер позиции (% от баланса)")
        else:
            self.position_size_label.setText("Размер позиции (фиксированная сумма в USDT)")

    def update_trade_position_size_label(self):
        if self.trade_position_type_combo.currentIndex() == 0:
            self.trade_position_size_label.setText("Размер позиции (% от баланса)")
        else:
            self.trade_position_size_label.setText("Размер позиции (фиксированная сумма в USDT)")

    def load_settings(self):
        # Загружаем настройки тестирования
        self.commission_input.setText(self.settings.value("commission", "0.0008"))
        self.initial_balance_input.setText(self.settings.value("initial_balance", "1000"))
        self.leverage_input.setText(self.settings.value("leverage", "2"))
        self.profit_factor_input.setText(self.settings.value("profit_factor", "1.5"))
        self.position_size_input.setText(self.settings.value("position_size", "100"))
        
        # Загружаем настройки торговли
        self.trade_leverage_input.setText(self.settings.value("trade_leverage", "2"))
        self.trade_profit_factor_input.setText(self.settings.value("trade_profit_factor", "1.5"))
        self.trade_position_size_input.setText(self.settings.value("trade_position_size", "100"))
        
        trade_position_type = self.settings.value("trade_position_type", "percent")
        self.trade_position_type_combo.setCurrentIndex(0 if trade_position_type == "percent" else 1)
        
        self.refresh_interval_input.setValue(int(self.settings.value("refresh_interval", "10")))

        self.position_type = self.settings.value("position_type", "percent")
        if self.position_type == "percent":
            self.position_type_combo.setCurrentIndex(0)
        else:
            self.position_type_combo.setCurrentIndex(1)

    def save_settings(self):
        try:
            # Проверяем и сохраняем настройки тестирования
            initial_balance = float(self.initial_balance_input.text())
            position_size = float(self.position_size_input.text())
            
            if self.position_type_combo.currentIndex() == 1:  # "Фиксированная сумма в USDT"
                if position_size > initial_balance:
                    QMessageBox.warning(self, "Ошибка", "Размер позиции не может превышать начальный баланс.")
                    return
            elif self.position_type_combo.currentIndex() == 0:  # "Проценты"
                if position_size > 100:
                    QMessageBox.warning(self, "Ошибка", "Размер позиции не может быть больше 100%.")
                    return

            # Сохраняем настройки тестирования
            self.settings.setValue("commission", self.commission_input.text())
            self.settings.setValue("initial_balance", self.initial_balance_input.text())
            self.settings.setValue("leverage", self.leverage_input.text())
            self.settings.setValue("profit_factor", self.profit_factor_input.text())
            self.settings.setValue("position_size", self.position_size_input.text())
            self.settings.setValue("position_type", "percent" if self.position_type_combo.currentIndex() == 0 else "fixed")

            # Проверяем торговые настройки
            trade_leverage = float(self.trade_leverage_input.text())
            trade_profit_factor = float(self.trade_profit_factor_input.text())
            trade_position_size = float(self.trade_position_size_input.text())

            if self.trade_position_type_combo.currentIndex() == 0 and trade_position_size > 100:
                QMessageBox.warning(self, "Ошибка", "Размер позиции для торговли не может быть больше 100%.")
                return

            # Сохраняем настройки торговли
            self.settings.setValue("trade_leverage", str(trade_leverage))
            self.settings.setValue("trade_profit_factor", str(trade_profit_factor))
            self.settings.setValue("trade_position_size", str(trade_position_size))
            self.settings.setValue("trade_position_type", 
                                "percent" if self.trade_position_type_combo.currentIndex() == 0 else "fixed")
            self.settings.setValue("refresh_interval", str(self.refresh_interval_input.value()))

            self.accept()
            
        except ValueError:
            QMessageBox.critical(self, "Error", "Проверьте, что в полях корректно указаны числа. Десятичная дробь должна писаться через точку.", QMessageBox.Ok)

    def validate_fields(self):
        try:
            # Проверка полей тестирования
            float(self.commission_input.text())
            float(self.initial_balance_input.text())
            float(self.leverage_input.text())
            float(self.profit_factor_input.text())
            float(self.position_size_input.text())
            
            # Если все проверки пройдены, сохраняем настройки
            self.save_settings()
        except ValueError:
            QMessageBox.critical(self, "Error", "Проверьте, что в полях корректно указаны числа. Десятичная дробь должна писаться через точку.", QMessageBox.Ok)