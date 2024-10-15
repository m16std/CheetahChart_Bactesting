from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit

class LogWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.log_area = QTextEdit(self)
        self.log_area.setReadOnly(True)
        layout = QVBoxLayout(self)
        layout.addWidget(self.log_area)
        self.setLayout(layout)

    def update_log(self, log):
        self.log_area.append(log)
