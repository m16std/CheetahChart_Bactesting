from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtGui import QPixmap, QPainter, QIcon, QColor

class TabSelectorWindow(QWidget):
    tab_selected = pyqtSignal(str)  # Сигнал для передачи выбранного типа вкладки

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def recolor_svg_icon(self, svg_path, color):
        renderer = QSvgRenderer(svg_path)
        pixmap = QPixmap(40, 40)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), QColor(color))  # Преобразуем строку цвета в QColor
        painter.end()
        return QIcon(pixmap)

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0) 
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignCenter)

        # Заголовок
        title_a = QLabel("Cheetos trading lab")
        title_a.setStyleSheet("font-size: 20px; margin-bottom: 10px;")
        title_a.setAlignment(Qt.AlignLeft)
        layout.addWidget(title_a)
        title_b = QLabel("Открыть")
        title_b.setStyleSheet("font-size: 16px; margin-bottom: 10px; color: #bbb;")
        title_b.setAlignment(Qt.AlignLeft)
        layout.addWidget(title_b)

        # Кнопки с одинаковым размером
        button_style = """
            QPushButton {
                min-width: 300px;
                min-height: 25px;
                font-size: 14px;
                margin: 1px;
                padding: 5px;
                border-radius: 5px;
                border: none;
                text-align: left;
                padding-left: 2px;
                color: #669FD3;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 20);
            }
        """

        # Создаем иконки с разными цветами
        strategy_icon = self.recolor_svg_icon("resources/chart2.svg", "#669FD3")  
        code_icon = self.recolor_svg_icon("resources/code.svg", "#669FD3")     
        visual_icon = self.recolor_svg_icon("resources/constructor.svg", "#669FD3")  
        optimization_icon = self.recolor_svg_icon("resources/speed.svg", "#669FD3")

        # Кнопки с иконками
        strategy_button = QPushButton("  Окно тестирования стратегий")
        strategy_button.setIcon(strategy_icon)
        strategy_button.setIconSize(QSize(24, 24)) 
        strategy_button.setStyleSheet(button_style)
        strategy_button.clicked.connect(lambda: self.tab_selected.emit("strategy"))
        layout.addWidget(strategy_button)

        optimization_button = QPushButton("   Окно оптимизации параметров стратегий")
        optimization_button.setIcon(optimization_icon)
        optimization_button.setIconSize(QSize(24, 24))
        optimization_button.setStyleSheet(button_style)
        optimization_button.clicked.connect(lambda: self.tab_selected.emit("optimization"))
        layout.addWidget(optimization_button)

        visual_button = QPushButton("   Конструктор стратегий")
        visual_button.setIcon(visual_icon)
        visual_button.setIconSize(QSize(24, 24))  
        visual_button.setStyleSheet(button_style)
        visual_button.clicked.connect(lambda: self.tab_selected.emit("visual"))
        layout.addWidget(visual_button)

        code_button = QPushButton("   Редактор кода")
        code_button.setIcon(code_icon)
        code_button.setIconSize(QSize(24, 24))  
        code_button.setStyleSheet(button_style)
        code_button.clicked.connect(lambda: self.tab_selected.emit("code"))
        layout.addWidget(code_button)

        self.setLayout(layout)
