from PyQt5.QtWidgets import QStyledItemDelegate
from PyQt5.QtCore import QRect

class PaddedItemDelegate(QStyledItemDelegate):
    def __init__(self, padding=5, height=35, parent=None):
        super().__init__(parent)
        self.padding = padding
        self.height = height

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        size.setHeight(self.height)  # Фиксированная высота элемента
        return size

    def paint(self, painter, option, index):
        painter.save()
        
        # Добавляем отступ сверху и слева
        option.rect = QRect(
            option.rect.x() + self.padding,  # Отступ слева
            option.rect.y() + self.padding,  # Отступ сверху
            option.rect.width() - 2 * self.padding,  # Уменьшаем ширину
            option.rect.height() - 2 * self.padding  # Уменьшаем высоту
        )
 
        super().paint(painter, option, index)
        painter.restore()
