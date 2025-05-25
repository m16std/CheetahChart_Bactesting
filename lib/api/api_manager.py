from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QMessageBox, QDialog
from lib.api.okx_trade_api import OKXApi
from lib.api.api_checker import APIChecker

class APIManager:
    def __init__(self):
        self.active_api = None
        self.load_active_api()

    def load_active_api(self):
        """Загружает активный API из настроек."""
        settings = QSettings("MyApp", "MyCompany")
        active_api_name = settings.value("active_api", None)

        if active_api_name:
            self.active_api = {
                "name": active_api_name,
                "key": settings.value(f"{active_api_name}_key"),
                "secret": settings.value(f"{active_api_name}_secret"),
                "passphrase": settings.value(f"{active_api_name}_passphrase")
            }
        else:
            self.active_api = None

    def get_api_instance(self):
        """Возвращает экземпляр API."""
        if self.active_api:
            return OKXApi(
                api_key=self.active_api["key"],
                api_secret=self.active_api["secret"],
                passphrase=self.active_api["passphrase"]
            )
        return None

    def open_api_settings_dialog(self, parent):
        """Открывает диалог настроек API."""
        from lib.windows.api_settings_window import APISettingsWindow
        dialog = APISettingsWindow(parent)
        if dialog.exec_() == QDialog.Accepted:
            self.load_active_api()

    def check_api_status(self, parent):
        """Проверяет доступность API."""
        if not self.active_api:
            QMessageBox.warning(parent, "Ошибка", "API не настроен. Пожалуйста, настройте API в разделе 'Настроить API'.")
            return

        success, result = APIChecker.check_api_status(
            api_key=self.active_api["key"],
            api_secret=self.active_api["secret"],
            passphrase=self.active_api["passphrase"]
        )

        if success:
            QMessageBox.information(parent, "Успех", f"API '{self.active_api['name']}' работает корректно.")
        else:
            QMessageBox.critical(parent, "Ошибка", f"API '{self.active_api['name']}' не отвечает. Ошибка: {result}")
