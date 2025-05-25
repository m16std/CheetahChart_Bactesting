from PyQt5.QtWidgets import QSplitter, QWidget
from PyQt5.QtCore import Qt

class SplitView(QSplitter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setChildrenCollapsible(False)
        self.setHandleWidth(1)
        self.setStyleSheet("""
            QSplitter::handle {
                background-color: #666666;
            }
            QSplitter::handle:hover {
                background-color: #999999;
            }
        """)

    def split(self, current_widget, new_widget, orientation=Qt.Horizontal):
        """
        :param current_widget: Текущий виджет, который уже находится в сплиттере
        :param new_widget: Новый виджет, который нужно добавить справа/снизу
        """
        self.setOrientation(orientation)

        # Просто добавляем новый виджет справа/снизу от текущего
        index = self.indexOf(current_widget)
        if index >= 0:
            self.insertWidget(index + 1, new_widget)
        
        # Устанавливаем равные размеры (конвертируем в целые числа)
        total = self.width() if orientation == Qt.Horizontal else self.height()
        self.setSizes([int(total/2), int(total/2)])
