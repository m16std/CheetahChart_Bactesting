from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QDialog
from PyQt5.QtGui import QColor
import qdarktheme

class PositionsTable(QDialog):
    def __init__(self, positions, current_theme, show_synced_column=False):
        super().__init__()
        self.setWindowTitle('Positions')
        self.setGeometry(100, 100, 1200, 800)
        if current_theme == "dark":
            qdarktheme.setup_theme(
                custom_colors={
                    "[dark]": {
                        "background": "#151924",
                        "primary": "#ffffff",
                        "primary>button.hoverBackground": "#669ff55c",
                        "primary>progressBar.background": "#669ff5",
                    }
                }
            )
                
        else:
            qdarktheme.setup_theme(current_theme)



        # Создаём таблицу
        self.table_widget = QTableWidget()
        self.table_widget.setRowCount(len(positions))
        self.table_widget.setColumnCount(14) 
        max_pnl = 0 
        if len(positions) > 0:
            max_pnl = max(abs(position['pnl']) for position in positions)

        # Устанавливаем заголовки столбцов
        self.table_widget.setHorizontalHeaderLabels([
            'ID', 'Side', 'Order Type', 'Status', 'Quantity', 'Leverage', 'TP Trigger', 'SL Trigger', 'Open Price', 
             'Close Price', 'Open Time', 'Close Time', 'PnL', 'Commission', 'Synced'
        ])

        # Заполняем таблицу данными о позициях
        for row, position in enumerate(positions):
            self.table_widget.setItem(row, 0, QTableWidgetItem(str(position['posId'])))
            self.table_widget.setItem(row, 1, QTableWidgetItem(position['posSide']))
            self.table_widget.setItem(row, 2, QTableWidgetItem(position['ordType']))
            self.table_widget.setItem(row, 3, QTableWidgetItem(position['status']))
            self.table_widget.setItem(row, 4, QTableWidgetItem(str(round(position['qty'], 1))))
            self.table_widget.setItem(row, 5, QTableWidgetItem(str(position['leverage'])))
            self.table_widget.setItem(row, 6, QTableWidgetItem(str(round(position['tpTriggerPx'], 1))))
            self.table_widget.setItem(row, 7, QTableWidgetItem(str(round(position['slTriggerPx'], 1))))
            self.table_widget.setItem(row, 8, QTableWidgetItem(str(round(position['openPrice'], 1))))
            self.table_widget.setItem(row, 9, QTableWidgetItem(str(round(position['closePrice'], 1))))
            self.table_widget.setItem(row, 10, QTableWidgetItem(str(position['openTimestamp'])))
            self.table_widget.setItem(row, 11, QTableWidgetItem(str(position['closeTimestamp'])))
            self.table_widget.setItem(row, 12, QTableWidgetItem(str(round(position['pnl'], 3))))
            self.table_widget.setItem(row, 13, QTableWidgetItem(str(round(position['commission'], 5))))
            if self.show_synced_column:
                self.table_widget.setItem(row, 14, QTableWidgetItem(str(position['synced'])))
            
            
            # Заполнение столбца с PnL и настройка цвета фона
            pnl_item = QTableWidgetItem(str(round(position['pnl'], 3)))
            pnl_value = position['pnl']

            # Расчет прозрачности в зависимости от отношения pnl/max_pnl
            if max_pnl != 0:
                transparency_factor = abs(pnl_value) / max_pnl
            else:
                transparency_factor = 1

            # Окрашиваем фон в зависимости от положительного или отрицательного PnL
            if pnl_value > 0:
                color = QColor(8, 153, 89)  # Зеленый
            elif pnl_value < 0:
                color = QColor(242, 54, 69)  # Красный
            else:
                color = QColor(0, 0, 0, 0)  # Нейтральный цвет для нуля

            # Устанавливаем прозрачность цвета
            color.setAlphaF(transparency_factor) 
            pnl_item.setBackground(color)
            self.table_widget.setItem(row, 12, pnl_item)


        # Настройка поведения таблицы
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Layout для окна
        layout = QVBoxLayout()
        layout.addWidget(self.table_widget)
        self.setLayout(layout)


