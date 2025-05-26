from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QMessageBox, QFrame, QHBoxLayout
from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtGui import QIcon

class APISettingsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки API")
        self.setMinimumWidth(300)
        self.settings = QSettings("MyApp", "MyCompany")
        self.layout = QVBoxLayout()
        self.layout.setSpacing(2)  # Уменьшаем отступы между элементами
        self.layout.setAlignment(Qt.AlignTop)  # Выравнивание по верхнему краю

        self.api_list_combo = QComboBox()
        self.load_api_list()

        # Добавляем горизонтальную линию
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)

        # Надпись "Добавление нового API" с выравниванием по центру
        add_api_label = QLabel("Добавление нового API")
        add_api_label.setAlignment(Qt.AlignCenter)

        self.api_name_input = QLineEdit()

        # Поле выбора биржи
        self.exchange_combo = QComboBox()
        self.exchange_combo.addItems(["OKX", "Binance", "Bybit"])  # Add more exchanges as needed

        # Поле API Key с кнопкой показа/скрытия символов
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)

        # Поле API Secret с кнопкой показа/скрытия символов
        self.api_secret_input = QLineEdit()
        self.api_secret_input.setEchoMode(QLineEdit.Password)

        # Поле Passphrase с кнопкой показа/скрытия символов
        self.passphrase_input = QLineEdit()
        self.passphrase_input.setEchoMode(QLineEdit.Password)

        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.save_api)

        delete_button = QPushButton("Удалить выбранный API")
        delete_button.clicked.connect(self.delete_api)

        # Группируем поля и их подписи
        for label_text, widget in [
            ("Выберите API:", self.api_list_combo),
            (None, separator),  # Разделитель
            (None, add_api_label),  # Заголовок "Добавление нового API"
            ("Имя API:", self.api_name_input),
            ("Биржа:", self.exchange_combo),
            ("API Key:", self.api_key_input),
            ("API Secret:", self.api_secret_input),
            ("Passphrase:", self.passphrase_input)
        ]:
            if widget == separator:
                self.layout.addWidget(widget)
                self.layout.addSpacing(5)
                continue
            
            if widget == add_api_label:
                self.layout.addWidget(widget)
                self.layout.addSpacing(5)
                continue

            field_layout = QVBoxLayout()
            field_layout.setSpacing(1)  # Минимальный отступ между меткой и полем
            
            if label_text:  # Если есть текст метки
                label = QLabel(label_text)
                field_layout.addWidget(label)
                if isinstance(widget, QLineEdit):  # Если это поле для пароля
                    field_layout.addLayout(self._create_password_field(widget))
                else:
                    field_layout.addWidget(widget)
            else:
                field_layout.addWidget(widget)
            
            self.layout.addLayout(field_layout)
            self.layout.addSpacing(5)  # Отступ между группами полей

        # Добавляем кнопки
        self.layout.addWidget(save_button)
        self.layout.addWidget(delete_button)

        self.setLayout(self.layout)
        self.api_list_combo.currentIndexChanged.connect(self.load_selected_api)

    def _create_password_field(self, line_edit):
        """Создает поле ввода с кнопкой показа/скрытия символов."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        line_edit.setStyleSheet("border-top-left-radius: 5px; border-bottom-left-radius: 5px;")
        layout.addWidget(line_edit)

        toggle_button = QPushButton()
        toggle_button.setIcon(QIcon("resources/eye.svg"))  # Изначально используется иконка "глаз"
        toggle_button.setCheckable(True)
        toggle_button.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: #f0f0f0;
                border-top-right-radius: 5px;
                border-bottom-right-radius: 5px;
            }
            QPushButton:checked {
                background-color: #d0d0d0;
            }
        """)
        toggle_button.setFixedWidth(30)
        toggle_button.toggled.connect(lambda checked: self._toggle_password_visibility(line_edit, toggle_button, checked))
        layout.addWidget(toggle_button)

        return layout

    def _toggle_password_visibility(self, line_edit, toggle_button, checked):
        """Переключает видимость текста и обновляет иконку кнопки."""
        line_edit.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
        toggle_button.setIcon(QIcon("resources/eye-slash.svg" if checked else "resources/eye.svg"))

    def load_api_list(self):
        self.api_list_combo.clear()
        api_list = self.settings.value("api_list", [])
        if api_list:
            self.api_list_combo.addItems(api_list)

    def load_selected_api(self):
        """Загружает данные выбранного API и сохраняет его как активный."""
        selected_api = self.api_list_combo.currentText()
        if selected_api:
            self.api_key_input.setText(self.settings.value(f"{selected_api}_key", ""))
            self.api_secret_input.setText(self.settings.value(f"{selected_api}_secret", ""))
            self.passphrase_input.setText(self.settings.value(f"{selected_api}_passphrase", ""))
            self.exchange_combo.setCurrentText(self.settings.value(f"{selected_api}_exchange", "OKX"))
            self.settings.setValue("active_api", selected_api)

    def save_api(self):
        api_name = self.api_name_input.text().strip()
        if not api_name:
            QMessageBox.warning(self, "Ошибка", "Введите имя API.")
            return

        self.settings.setValue(f"{api_name}_key", self.api_key_input.text())
        self.settings.setValue(f"{api_name}_secret", self.api_secret_input.text())
        self.settings.setValue(f"{api_name}_passphrase", self.passphrase_input.text())
        self.settings.setValue(f"{api_name}_exchange", self.exchange_combo.currentText())

        api_list = self.settings.value("api_list", [])
        if not api_list:
            api_list = []
        if api_name not in api_list:
            api_list.append(api_name)
            self.settings.setValue("api_list", api_list)

        QMessageBox.information(self, "Успех", "API сохранен.")
        self.load_api_list()
        self.api_name_input.clear()

    def delete_api(self):
        api_name = self.api_list_combo.currentText()
        if not api_name:
            QMessageBox.warning(self, "Ошибка", "Выберите API для удаления.")
            return

        self.settings.remove(f"{api_name}_key")
        self.settings.remove(f"{api_name}_secret")
        self.settings.remove(f"{api_name}_passphrase")
        self.settings.remove(f"{api_name}_exchange")

        api_list = self.settings.value("api_list", [])
        if api_name in api_list:
            api_list.remove(api_name)
            self.settings.setValue("api_list", api_list)

        QMessageBox.information(self, "Успех", "API удален.")
        self.load_api_list()
