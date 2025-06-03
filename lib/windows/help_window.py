from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextBrowser
from PyQt5.QtCore import Qt

class HelpWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Пользовательское соглашение")
        self.setMinimumWidth(1000)
        self.setMinimumHeight(800)
        
        layout = QVBoxLayout(self)
        
        self.text_browser = QTextBrowser()
        self.text_browser.setStyleSheet("border: 0px")
        self.text_browser.setOpenExternalLinks(True) 
        layout.addWidget(self.text_browser)
        
        # Загружаем HTML файл
        self.load_help_content()
        
    def load_help_content(self):
        try:
            with open('resources/user_agreement.htm', 'r', encoding='windows-1251') as file:
                html_content = file.read()
                self.text_browser.setHtml(html_content)
        except FileNotFoundError:
            self.text_browser.setPlainText("Файл пользовательского соглашения не найден.")