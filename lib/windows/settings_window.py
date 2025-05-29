from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
                           QComboBox, QMessageBox, QSpinBox, QTabWidget, QWidget, QFrame, QHBoxLayout)
from PyQt5.QtCore import Qt
from lib.windows.api_settings_window import APISettingsWindow  # Добавляем импорт

class SettingsWindow(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Настройки")
        self.setMinimumWidth(400)

        # Основной макет окна
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Создаем TabWidget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Создаем и инициализируем вкладки
        self.init_tabs()

        # Кнопка сохранения
        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.validate_fields)
        main_layout.addWidget(save_button)

        self.load_settings()

    def init_tabs(self):
        """Инициализация всех вкладок"""
        # Создаем вкладки
        self.testing_tab = QWidget()
        self.trading_tab = QWidget()
        self.data_source_tab = QWidget()
        self.api_settings_tab = QWidget()

        # Создаем макеты для каждой вкладки
        testing_layout = QVBoxLayout(self.testing_tab)
        trading_layout = QVBoxLayout(self.trading_tab)
        data_source_layout = QVBoxLayout(self.data_source_tab)
        api_settings_layout = QVBoxLayout(self.api_settings_tab)

        # Добавляем вкладки в TabWidget
        self.tab_widget.addTab(self.testing_tab, "Тестирование")
        self.tab_widget.addTab(self.trading_tab, "Торговля")
        self.tab_widget.addTab(self.data_source_tab, "Источники данных")
        self.tab_widget.addTab(self.api_settings_tab, "Настройки API")

        # Инициализируем содержимое вкладок
        self.init_testing_tab(testing_layout)
        self.init_trading_tab(trading_layout)
        self.init_data_source_tab(data_source_layout)
        self.init_api_settings_tab(api_settings_layout)

    def init_testing_tab(self, layout):
        """Инициализация вкладки тестирования"""
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

        layout.setSpacing(2)  # Уменьшаем расстояние между элементами
        layout.setAlignment(Qt.AlignTop)  # Выравнивание по верхнему краю

        # Группируем поля и их подписи
        for label_text, widget in [
            ("Торговая комиссия", self.commission_input),
            ("Начальный баланс (USDT)", self.initial_balance_input),
            ("Торговое плечо", self.leverage_input),
            ("Профит фактор", self.profit_factor_input),
            ("Тип размера позиции", self.position_type_combo),
            (None, self.position_size_label),  # None означает, что метка уже существует
            (None, self.position_size_input)
        ]:
            field_layout = QVBoxLayout()
            field_layout.setSpacing(1)  # Минимальный отступ между меткой и полем
            if label_text:  # Если есть текст метки
                label = QLabel(label_text)
                field_layout.addWidget(label) 
                field_layout.addWidget(widget) 
            else:  # Для существующих меток
                field_layout.addWidget(widget)
            
            layout.addLayout(field_layout)
            layout.addSpacing(5)  # Отступ между группами полей

    def init_trading_tab(self, layout):
        """Инициализация вкладки торговли"""
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

        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignTop)

        for label_text, widget in [
            ("Торговое плечо", self.trade_leverage_input),
            ("Профит фактор", self.trade_profit_factor_input),
            ("Тип размера позиции", self.trade_position_type_combo),
            (None, self.trade_position_size_label),
            (None, self.trade_position_size_input),
            ("Интервал обновления (сек):", self.refresh_interval_input)
        ]:
            field_layout = QVBoxLayout()
            field_layout.setSpacing(1)
            if label_text:
                label = QLabel(label_text)
                field_layout.addWidget(label)  # Сначала добавляем метку
                field_layout.addWidget(widget)  # Затем поле ввода
            else:
                field_layout.addWidget(widget)
            
            layout.addLayout(field_layout)
            layout.addSpacing(5)

    def init_data_source_tab(self, layout):
        """Инициализация вкладки выбора источника данных"""
        self.data_source_combo = QComboBox()
        self.data_source_combo.addItems(["OKX", "Binance", "Bybit"])

        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(2)

        field_layout = QVBoxLayout()
        field_layout.setSpacing(1)
        field_layout.addWidget(QLabel("Выберите источник данных:"))  # Сначала метка
        field_layout.addWidget(self.data_source_combo)  # Затем комбобокс
        layout.addLayout(field_layout)

    def init_api_settings_tab(self, layout):
        """Инициализация вкладки настройки API"""
        # Создаем экземпляр окна настроек API
        api_settings = APISettingsWindow()
        
        # Добавляем его содержимое в наш layout
        layout.addWidget(api_settings)
        
        # Удаляем заголовок и рамку окна, так как оно встроено
        api_settings.setWindowFlags(Qt.Widget)
        
        # Сохраняем ссылку на окно настроек API
        self.api_settings = api_settings

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

        # Загрузка настроек для вкладки источников данных
        self.data_source_combo.setCurrentText(self.settings.value("data_source", "OKX"))

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

            # Сохранение настроек для вкладки источников данных
            self.settings.setValue("data_source", self.data_source_combo.currentText())

            # Сохранение настроек для вкладки API
            self.settings.setValue("api_name", self.api_settings.api_name_input.text())
            self.settings.setValue("api_key", self.api_settings.api_key_input.text())
            self.settings.setValue("api_secret", self.api_settings.api_secret_input.text())
            self.settings.setValue("api_passphrase", self.api_settings.passphrase_input.text())

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