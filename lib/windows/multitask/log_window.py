from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit

class LogWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Логи")
        self.setMinimumWidth(250)
        self.setMinimumHeight(300)

        self.layout = QVBoxLayout(self)
        self.log_text_edit = QTextEdit(self)
        self.log_text_edit.setReadOnly(True)
        self.layout.addWidget(self.log_text_edit)

    def load_logs(self, log_file='trading_log.txt'):
        """Загружает содержимое текстового файла лога в окно логов и прокручивает вниз."""
        try:
            with open(log_file, 'r') as file:
                self.log_text_edit.setText(file.read())
            self.scroll_to_bottom()  # Прокрутка вниз
        except Exception as e:
            self.log_text_edit.setText(f"Ошибка загрузки логов: {e}")

    def add_log_entry(self, entry):
        """Добавляет новую строку в окно логов и прокручивает вниз."""
        self.log_text_edit.append(entry)
        self.scroll_to_bottom()  # Прокрутка вниз

    def scroll_to_bottom(self):
        """Прокручивает видимую область окна логов вниз."""
        self.log_text_edit.moveCursor(self.log_text_edit.textCursor().End)
