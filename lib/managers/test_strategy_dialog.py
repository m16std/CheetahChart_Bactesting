from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt

class TestStrategyDialog(QDialog):
    def __init__(self, trading_apps, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выберите редактор для тестирования")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Заголовок
        title = QLabel("В каком редакторе запустить тестирование?")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Добавляем кнопки для каждого открытого редактора
        for i, app in enumerate(trading_apps):
            tab_name = app.strat_input.currentText() if hasattr(app, 'strat_input') else f"Редактор {i+1}"
            button = QPushButton(f"{tab_name}")
            button.clicked.connect(lambda checked, idx=i: self.done(idx + 1))
            layout.addWidget(button)
        
        # Кнопка для создания нового редактора
        new_button = QPushButton("Создать новый редактор")
        new_button.clicked.connect(lambda: self.done(len(trading_apps) + 1))
        layout.addWidget(new_button)
        
        # Кнопка отмены
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(cancel_button)
        
        self.setLayout(layout)











